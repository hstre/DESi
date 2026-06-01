"""Q4/Q8 × Raw/DESi-State Minimaltest.

Four conditions on 30 stratified LongMemEval items:
  A. Granite 4.1 8B  + Raw Context  (≈ "Q8 + raw")
  B. Granite 4.0 H-Micro + Raw Context  (≈ "Q4 + raw")
  C. Granite 4.1 8B  + DESi-State (oracle evidence sessions only)  (≈ "Q8 + state")
  D. Granite 4.0 H-Micro + DESi-State  (≈ "Q4 + state")

Key comparison: D vs A — can a smaller/cheaper model + state match the
full-context performance of a larger model?

NB: This uses model tier (8B vs 3B-class) as a proxy for Q8 vs Q4 because
OpenRouter does not expose quantization variants directly.

Scoring: substring match (gold_answer in response, case-insensitive).
No LLM judge — deterministic, comparable across runs.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "results" / "minimaltest_q4_q8"
_OUT.mkdir(parents=True, exist_ok=True)
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)

DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

MODELS = {
    "ibm-granite/granite-4.1-8b": "Q8-proxy",
    "ibm-granite/granite-4.0-h-micro": "Q4-proxy",
}

N_PER_TYPE = 5
SEED = 42
PARALLELISM = 4

SYSTEM = ("You are an assistant who answers questions based on the provided "
          "conversation history. Read the history carefully, then answer "
          "concisely. If the answer isn't in the history, say so.")


def build_user_message(item, variant):
    sessions = item["haystack_sessions"]
    session_ids = item["haystack_session_ids"]
    evidence = set(item["answer_session_ids"])
    if variant == "raw":
        chosen = list(zip(sessions, session_ids))
    else:  # "state" = oracle DESi-State (evidence sessions only)
        chosen = [(s, sid) for s, sid in zip(sessions, session_ids) if sid in evidence]
    parts = ["=== CONVERSATION HISTORY ==="]
    for sess, sid in chosen:
        parts.append(f"\n--- session {sid} ---")
        for turn in sess:
            role = turn.get("role", "user").upper()
            parts.append(f"{role}: {turn.get('content','')}")
    parts.append("\n=== CURRENT QUESTION ===")
    parts.append(item["question"])
    return "\n".join(parts)


def _http_post(url, headers, body, timeout=240, retries=3):
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


def call_openrouter(model, system, user, max_tokens=256):
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
         "X-Title": "DESi Q4/Q8 Minimaltest"},
        body,
    )
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "",
                "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


def score_substring(response_text: str, gold_answer: str) -> float:
    if not response_text:
        return 0.0
    return 1.0 if gold_answer.lower() in response_text.lower() else 0.0


def run_one(item, model, variant):
    user = build_user_message(item, variant)
    r = call_openrouter(model, SYSTEM, user, max_tokens=256)
    return {
        "model": model,
        "variant": variant,
        "response_text": r.get("text", ""),
        "input_tokens": r.get("input_tokens"),
        "output_tokens": r.get("output_tokens"),
        "latency_ms": r.get("latency_ms"),
        "error": r.get("error"),
        "score": score_substring(r.get("text", ""), item["answer"]),
        "context_len_chars": len(user),
    }


def run_item(item):
    item_path = _ITEMS_OUT / f"{item['question_id']}.json"
    if item_path.exists():
        return item["question_id"]
    rec = {
        "question_id": item["question_id"],
        "question_type": item["question_type"],
        "question": item["question"],
        "gold_answer": item["answer"],
        "n_sessions": len(item["haystack_sessions"]),
        "n_evidence_sessions": sum(1 for sid in item["haystack_session_ids"]
                                   if sid in set(item["answer_session_ids"])),
        "runs": [],
    }
    for model in MODELS:
        for variant in ("raw", "state"):
            rec["runs"].append(run_one(item, model, variant))
    item_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return item["question_id"]


def sample_stratified(data, n_per_type=5, seed=42):
    by_type = defaultdict(list)
    for item in data:
        by_type[item["question_type"]].append(item)
    rng = random.Random(seed)
    sampled = []
    for qt, items in sorted(by_type.items()):
        sampled.extend(rng.sample(items, min(n_per_type, len(items))))
    return sampled


def main():
    print(f"Loading {DATASET} ...", flush=True)
    data = json.loads(DATASET.read_text())
    print(f"  Total items: {len(data)}", flush=True)
    sampled = sample_stratified(data, N_PER_TYPE, SEED)
    print(f"  Sampled (stratified, seed={SEED}): {len(sampled)}", flush=True)
    by_type = defaultdict(int)
    for it in sampled:
        by_type[it["question_type"]] += 1
    for qt, n in sorted(by_type.items()):
        print(f"    {qt}: {n}", flush=True)

    print(f"\nRunning {len(sampled)} items × 2 models × 2 variants = "
          f"{len(sampled)*4} API calls, parallelism={PARALLELISM}", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, it): it["question_id"] for it in sampled}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 3 == 0 or done <= 2:
                    print(f"  [{done}/{len(sampled)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {e}", flush=True)
    print(f"\nDone. {done}/{len(sampled)} items written.", flush=True)


if __name__ == "__main__":
    main()
