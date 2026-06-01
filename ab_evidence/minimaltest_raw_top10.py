"""Raw top-10 baseline: skip extraction entirely.

For each item:
  1. Use the SAME top-10 session selection from the hybrid run (embedding cosine)
  2. Concatenate those 10 sessions' raw text (chronological order)
  3. Feed to Q4 and Q8 answerers — no extraction, no evidence cards
  4. Score

This isolates: "Is the bottleneck retrieval, extraction, or the small answerer itself?"
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HYBRID_ITEMS = _HERE / "results" / "minimaltest_hybrid" / "items"
_OUT = _HERE / "results" / "minimaltest_raw_top10"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

ANSWERER_MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
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
         "X-Title": "DESi RawTop10"}, body)
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


def build_raw_top10_context(item_raw, chosen_session_ids):
    """Concatenate the top-10 sessions in chronological order (= order in haystack)."""
    sessions = item_raw["haystack_sessions"]
    sids = item_raw["haystack_session_ids"]
    sid_to_idx = {sid: i for i, sid in enumerate(sids)}
    indices_chrono = sorted([sid_to_idx[sid] for sid in chosen_session_ids if sid in sid_to_idx])
    parts = ["=== CONVERSATION EXCERPTS (chronological) ==="]
    for idx in indices_chrono:
        parts.append(f"\n--- session {sids[idx]} ---")
        for turn in sessions[idx]:
            parts.append(f"{turn.get('role','user').upper()}: {turn.get('content','')}")
    return "\n".join(parts)


def run_item(item_raw, hybrid_item):
    qid = item_raw["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    if out_path.exists():
        return qid

    chosen = hybrid_item["hybrid_extraction"]["chosen_session_ids"]
    ctx = build_raw_top10_context(item_raw, chosen)
    user = f"{ctx}\n\n=== QUESTION ===\n{item_raw['question']}\n\nAnswer:"

    rec = {
        "question_id": qid,
        "question_type": item_raw["question_type"],
        "question": item_raw["question"],
        "gold_answer": item_raw["answer"],
        "n_sessions": len(item_raw["haystack_sessions"]),
        "n_chosen": len(chosen),
        "chosen_session_ids": chosen,
        "evidence_recall": hybrid_item["hybrid_extraction"]["evidence_recall"],
        "context_len_chars": len(ctx),
        "runs": [],
    }
    gold = item_raw["answer"]
    for model in ANSWERER_MODELS:
        r = call_or(model, SYSTEM, user, max_tokens=256)
        text = r.get("text", "") or ""
        score = 1.0 if gold.lower() in text.lower() else 0.0
        rec["runs"].append({
            "model": model,
            "state_type": "raw_top10",
            "response_text": text,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
            "score": score,
        })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


def main():
    print("Loading dataset and hybrid items...", flush=True)
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid = sorted(_HYBRID_ITEMS.glob("*.json"))
    items = [json.loads(p.read_text()) for p in hybrid]
    print(f"  {len(items)} hybrid items loaded", flush=True)

    pairs = []
    for h in items:
        qid = h["question_id"]
        if qid in by_qid:
            pairs.append((by_qid[qid], h))
        else:
            print(f"  WARNING: {qid} not in dataset", flush=True)

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
