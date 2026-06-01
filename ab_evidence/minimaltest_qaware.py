"""Variante 3: Question-Aware Extraction.

Extractor task is brutally narrow: given the question and one session, output ONLY
- sentences that DIRECTLY answer the question, OR
- sentences that contradict / supersede an earlier answer

Output schema is question-bound, not generic:
  {
    "direct_quote": "...",       # exact substring of the session
    "session_id": "...",
    "is_update": true|false      # does this supersede earlier info?
  }

The model is not asked to summarize, abstract, or evaluate evidence. Just find the
question-relevant sentence(s) and quote them.

Compare to:
- Raw top-10 (best previous result, Q4 = 0.40)
- Oracle (upper bound, Q4 = 0.48)
- DESi-LLM v2 (general extraction, Q4 = 0.20)
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HYBRID_ITEMS = _HERE / "results" / "minimaltest_hybrid" / "items"
_OUT = _HERE / "results" / "minimaltest_qaware"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

ANSWERER_MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
EXTRACTOR_MODEL = "ibm-granite/granite-4.0-h-micro"
PARALLELISM = 4

SYSTEM_EXTRACT = (
    "You find the sentence(s) in ONE conversation session that DIRECTLY answer "
    "or contradict a specific question.\n\n"
    "Do NOT:\n"
    "- summarize the session\n"
    "- explain the question\n"
    "- output your own commentary\n"
    "- output anything that is not a verbatim quote from the session\n\n"
    "Output: a JSON array of objects with this shape:\n"
    '  {"direct_quote": "verbatim substring", "is_update": true|false}\n\n'
    "If NO sentence in this session directly answers or contradicts the question, output: []\n\n"
    "Set is_update=true ONLY if the sentence updates / overrides / contradicts an "
    "earlier piece of information the user had stated."
)

SYSTEM_ANSWER = (
    "You answer a question using a list of direct quotes extracted from a long "
    "conversation, in chronological order (oldest first). When quotes conflict, "
    "the LATER quote reflects an update; trust the most recent. Be concise."
)


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


def call_or(model, system, user, max_tokens=400):
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
         "X-Title": "DESi QAware"}, body)
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


_JSON_RE = re.compile(r"\[.*\]", re.DOTALL)


def parse_quotes(text):
    if not text:
        return []
    m = _JSON_RE.search(text)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
        if not isinstance(arr, list):
            return []
        out = []
        for e in arr:
            if isinstance(e, dict) and "direct_quote" in e:
                out.append({"direct_quote": str(e["direct_quote"]),
                            "is_update": bool(e.get("is_update", False))})
        return out
    except Exception:
        return []


def validate_quote(q, session_str):
    qs = q.get("direct_quote", "").strip()
    if len(qs) < 5:
        return False
    if qs in session_str:
        return True
    return re.sub(r"\s+", " ", qs) in re.sub(r"\s+", " ", session_str)


def extract_one_session(question, sess, sid):
    sess_str = session_text(sess)
    user = (f"QUESTION: {question}\n\n"
            f"SESSION:\n{sess_str}\n\n"
            f'Output JSON array (or [] if nothing directly answers):')
    r = call_or(EXTRACTOR_MODEL, SYSTEM_EXTRACT, user, max_tokens=300)
    parsed = parse_quotes(r.get("text", ""))
    validated = []
    rejected = 0
    for q in parsed:
        if validate_quote(q, sess_str):
            q["session_id"] = sid
            validated.append(q)
        else:
            rejected += 1
    return {
        "session_id": sid,
        "raw_output": (r.get("text", "") or "")[:400],
        "quotes_extracted": len(parsed),
        "quotes_validated": len(validated),
        "quotes_rejected": rejected,
        "validated_quotes": validated,
        "input_tokens": r.get("input_tokens"),
        "output_tokens": r.get("output_tokens"),
        "error": r.get("error"),
    }


def run_item(item_raw, hybrid_item):
    qid = item_raw["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    if out_path.exists():
        return qid

    chosen = hybrid_item["hybrid_extraction"]["chosen_session_ids"]
    sids = item_raw["haystack_session_ids"]
    sessions = item_raw["haystack_sessions"]
    sid_to_idx = {sid: i for i, sid in enumerate(sids)}

    # Process top-10 in chronological order
    indices_chrono = sorted([sid_to_idx[sid] for sid in chosen if sid in sid_to_idx])

    per_session = []
    all_quotes = []
    for idx in indices_chrono:
        res = extract_one_session(item_raw["question"], sessions[idx], sids[idx])
        per_session.append(res)
        all_quotes.extend(res["validated_quotes"])

    # Build context for answerer
    if not all_quotes:
        ctx = "(No direct-answer quotes found in the top-10 retrieved sessions.)"
    else:
        parts = ["EXTRACTED QUOTES (chronological):"]
        for q in all_quotes:
            tag = " [UPDATE]" if q.get("is_update") else ""
            parts.append(f"- [session {q['session_id']}]{tag} \"{q['direct_quote'][:300]}\"")
        ctx = "\n".join(parts)

    user = f"{ctx}\n\n=== QUESTION ===\n{item_raw['question']}\n\nAnswer:"

    rec = {
        "question_id": qid,
        "question_type": item_raw["question_type"],
        "question": item_raw["question"],
        "gold_answer": item_raw["answer"],
        "n_sessions": len(sessions),
        "n_chosen": len(chosen),
        "chosen_session_ids": chosen,
        "evidence_recall": hybrid_item["hybrid_extraction"]["evidence_recall"],
        "qaware_extraction": {
            "n_quotes_total": len(all_quotes),
            "n_sessions_with_quotes": sum(1 for s in per_session if s["quotes_validated"] > 0),
            "n_hallucinated": sum(s["quotes_rejected"] for s in per_session),
            "per_session": per_session,
        },
        "context_text_preview": ctx[:500],
        "runs": [],
    }
    gold = item_raw["answer"]
    for model in ANSWERER_MODELS:
        r = call_or(model, SYSTEM_ANSWER, user, max_tokens=256)
        text = r.get("text", "") or ""
        score = 1.0 if gold.lower() in text.lower() else 0.0
        rec["runs"].append({
            "model": model,
            "state_type": "qaware",
            "response_text": text,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
            "score": score,
            "context_len_chars": len(user),
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
