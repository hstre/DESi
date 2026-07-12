"""Extend the k* (optimal evidence density) table to the full red-team roster.

Same protocol as ``minimaltest_model_sweep.py`` — same 30 stratified LongMemEval-S
items, same embedding top-k selection (verified to reproduce the stored
chosen_session_ids exactly), same chronological ordering, same substring scoring,
k in {3, 5, 8, 10}. Only the model list differs: the 12 roster models that were
tested on hard/hard2 but never k*-characterized.

Already in the table (measured earlier, not re-run here): granite-4.0-h-micro (k*=3),
granite-4.1-8b (k*=10).

Reads OPENROUTER_API_KEY from env — never embedded/logged/committed. Resumable:
skips (item, k, model) triples already recorded. Writes to a SEPARATE results dir
so the original 6-model measurement stays untouched.

    OPENROUTER_API_KEY="$(cat keyfile)" python minimaltest_kstar_roster.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minimaltest_model_sweep import (  # noqa: E402
    K_VALUES,
    SYSTEM,
    build_context,
    call_or,
    topk_sessions_by_sim,
)

_HERE = Path(__file__).resolve().parent
_HYBRID_ITEMS = _HERE / "results" / "minimaltest_hybrid" / "items"
_OUT = _HERE / "results" / "minimaltest_kstar_roster"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"
PARALLELISM = 6

# The red-team roster's OpenRouter ids (hard/hard2), minus the two Granite models
# already in the k* table.
ROSTER_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-2.5-pro",
    "x-ai/grok-4.5",
    "google/gemma-4-31b-it",
    "poolside/laguna-m.1",
    "z-ai/glm-5.2",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-chat-v3.1",
    "qwen/qwen3-next-80b-a3b-instruct",
    "google/gemma-3-12b-it",
    "qwen/qwen3-30b-a3b",
    "mistralai/ministral-8b-2512",
]

# Reasoning models (gpt-5.1, grok-4.5, …) can spend the completion budget on hidden
# reasoning tokens; give enough headroom that the visible answer still fits. Uniform
# across models — non-reasoning ones stop early, so it does not change their output.
MAX_TOKENS = 800


def run_one(item_raw, hybrid_item):
    qid = item_raw["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    rec = {
        "question_id": qid,
        "question_type": item_raw["question_type"],
        "question": item_raw["question"],
        "gold_answer": item_raw["answer"],
        "evidence_session_ids": list(item_raw["answer_session_ids"]),
        "runs_by_k": {},
    }
    if out_path.exists():
        rec = json.loads(out_path.read_text())

    evidence_set = set(item_raw["answer_session_ids"])
    gold = item_raw["answer"]

    for k in K_VALUES:
        kstr = str(k)
        if kstr not in rec["runs_by_k"]:
            chosen = topk_sessions_by_sim(hybrid_item, k)
            recall = sum(1 for sid in chosen if sid in evidence_set) / max(1, len(evidence_set))
            rec["runs_by_k"][kstr] = {
                "chosen_session_ids": chosen,
                "evidence_recall": recall,
                "runs": [],
            }
        chosen = rec["runs_by_k"][kstr]["chosen_session_ids"]
        ctx = build_context(item_raw, chosen)
        user = f"{ctx}\n\n=== QUESTION ===\n{item_raw['question']}\n\nAnswer:"
        existing_models = {r["model"] for r in rec["runs_by_k"][kstr]["runs"]}
        for model in ROSTER_MODELS:
            if model in existing_models:
                continue
            r = call_or(model, SYSTEM, user, max_tokens=MAX_TOKENS)
            text = r.get("text", "") or ""
            score = 1.0 if gold.lower() in text.lower() else 0.0
            rec["runs_by_k"][kstr]["runs"].append({
                "model": model,
                "response_text": text,
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                "score": score,
            })
        out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


def main() -> int:
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid = sorted(_HYBRID_ITEMS.glob("*.json"))
    items = [json.loads(p.read_text()) for p in hybrid]
    pairs = [(by_qid[h["question_id"]], h) for h in items if h["question_id"] in by_qid]
    print(f"{len(pairs)} items x {len(K_VALUES)} k x {len(ROSTER_MODELS)} models", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_one, raw, h): raw["question_id"] for raw, h in pairs}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                print(f"  [{done}/{len(pairs)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {type(e).__name__}: {e}", flush=True)
    print(f"Done. {done}/{len(pairs)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
