"""Top-k retrieval curve: how much evidence does the small model actually need?

For each of the 30 stratified LongMemEval items:
  1. Reuse the embedding similarity scores from the hybrid run
  2. For k in {3, 5, 8} (top-10 already exists from raw_top10 run):
     - Take top-k sessions by similarity
     - Re-order chronologically (oldest first)
     - Build raw context from those k sessions
     - Run Q4 and Q8 answerers
  3. Score by substring match

Produces the curve: score(Q4|k=3), score(Q4|k=5), score(Q4|k=8), score(Q4|k=10).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HYBRID_ITEMS = _HERE / "results" / "minimaltest_hybrid" / "items"
_OUT = _HERE / "results" / "minimaltest_topk_curve"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
K_VALUES = [3, 5, 8]  # top-10 already in minimaltest_raw_top10
PARALLELISM = 4

SYSTEM = ("You are an assistant who answers questions based on the provided "
          "conversation excerpts. The excerpts are listed in chronological order; "
          "when facts conflict, trust the most recent. Answer concisely. "
          "If the excerpts don't contain the answer, say so.")


def _http_post(url, headers, body, timeout=180, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:400]
            if e.code in (400, 401, 403, 404):
                return {"_http_error": e.code, "_body": text}
            last = f"HTTP {e.code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


def call_or(model, system, user, max_tokens=256):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return {"error": "no OPENROUTER_API_KEY", "text": ""}
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
    }).encode()
    t0 = time.time()
    d = _http_post(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {key}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://github.com/hstre/DESi",
         "X-Title": "DESi TopK Curve"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "", "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def topk_sessions_by_sim(hybrid_item, k):
    """Get top-k session_ids by similarity (from hybrid's per_session data)."""
    per_sess = hybrid_item["hybrid_extraction"]["per_session"]
    # Sort by similarity desc
    sorted_sess = sorted(per_sess, key=lambda s: -s.get("embedding_sim", 0.0))
    return [s["session_id"] for s in sorted_sess[:k]]


def build_context(item_raw, chosen_ids):
    sessions = item_raw["haystack_sessions"]
    sids = item_raw["haystack_session_ids"]
    sid_to_idx = {sid: i for i, sid in enumerate(sids)}
    indices_chrono = sorted([sid_to_idx[sid] for sid in chosen_ids if sid in sid_to_idx])
    parts = ["=== CONVERSATION EXCERPTS (chronological) ==="]
    for idx in indices_chrono:
        parts.append(f"\n--- session {sids[idx]} ---")
        for turn in sessions[idx]:
            parts.append(f"{turn.get('role','user').upper()}: {turn.get('content','')}")
    return "\n".join(parts), len(indices_chrono)


def run_item(item_raw, hybrid_item):
    qid = item_raw["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    if out_path.exists():
        return qid

    rec = {
        "question_id": qid,
        "question_type": item_raw["question_type"],
        "question": item_raw["question"],
        "gold_answer": item_raw["answer"],
        "n_sessions": len(item_raw["haystack_sessions"]),
        "evidence_session_ids": list(item_raw["answer_session_ids"]),
        "runs_by_k": {},
    }

    evidence_set = set(item_raw["answer_session_ids"])
    gold = item_raw["answer"]

    for k in K_VALUES:
        chosen = topk_sessions_by_sim(hybrid_item, k)
        ctx, n_chosen = build_context(item_raw, chosen)
        recall = sum(1 for sid in chosen if sid in evidence_set) / max(1, len(evidence_set))
        user = f"{ctx}\n\n=== QUESTION ===\n{item_raw['question']}\n\nAnswer:"
        runs = []
        for model in MODELS:
            r = call_or(model, SYSTEM, user, max_tokens=256)
            text = r.get("text", "") or ""
            score = 1.0 if gold.lower() in text.lower() else 0.0
            runs.append({
                "model": model,
                "response_text": text,
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                "score": score,
            })
        rec["runs_by_k"][str(k)] = {
            "chosen_session_ids": chosen,
            "evidence_recall": recall,
            "context_len_chars": len(ctx),
            "runs": runs,
        }
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


def main():
    print("Loading dataset and hybrid items...", flush=True)
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid = sorted(_HYBRID_ITEMS.glob("*.json"))
    items = [json.loads(p.read_text()) for p in hybrid]
    print(f"  {len(items)} hybrid items loaded", flush=True)
    pairs = [(by_qid[h["question_id"]], h) for h in items if h["question_id"] in by_qid]

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, raw, h): raw["question_id"] for raw, h in pairs}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 5 == 0 or done <= 2:
                    print(f"  [{done}/{len(pairs)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {type(e).__name__}: {e}", flush=True)
    print(f"\nDone. {done}/{len(pairs)}", flush=True)


if __name__ == "__main__":
    main()
