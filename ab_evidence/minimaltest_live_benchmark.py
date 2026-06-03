"""Live end-to-end benchmark of the DESi pipeline.

Compares 4 strategies on 25 scorable LongMemEval-S items:
  1. Naive-Big:   always Granite 4.1 8B + full conversation context
  2. Naive-Small: always Granite Micro + top-3 retrieval
  3. DESi v0.2:   classify -> route, no escalation
  4. DESi v0.3:   classify -> route -> escalate if confidence low

For each strategy:
  - End-to-end accuracy (substring match against gold answer)
  - Total cost
  - Total latency
  - Cost per correct answer
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from desi.pipeline import DESiPipeline
from desi.answerer import answer as call_answerer

_HYBRID = _HERE / "results" / "minimaltest_hybrid" / "items"
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"
_OUT = _HERE / "results" / "minimaltest_live_benchmark"
(_OUT / "items").mkdir(parents=True, exist_ok=True)

_EMBED = None


def embed():
    global _EMBED
    if _EMBED is None:
        _EMBED = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED


def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def conv_text(sessions, ids):
    parts = ["=== CONVERSATION EXCERPTS (chronological) ==="]
    for s, sid in zip(sessions, ids):
        parts.append(f"\n--- session {sid} ---")
        for t in s:
            parts.append(f"{t.get('role','user').upper()}: {t.get('content','')}")
    return "\n".join(parts)


def topk_chronological(item_raw, hybrid_item, k):
    """Top-k by similarity (from hybrid per_session), then sorted chronologically."""
    per = hybrid_item["hybrid_extraction"]["per_session"]
    top_ids = [s["session_id"] for s in sorted(per, key=lambda x: -x["embedding_sim"])[:k]]
    sids = item_raw["haystack_session_ids"]
    idx_chrono = sorted(i for i, sid in enumerate(sids) if sid in top_ids)
    return ([item_raw["haystack_sessions"][i] for i in idx_chrono],
            [sids[i] for i in idx_chrono])


def build_haystack(item_raw, hybrid_item, strategy: str, k):
    """Build context block according to strategy + k."""
    if strategy == "raw_full":
        return conv_text(item_raw["haystack_sessions"], item_raw["haystack_session_ids"])
    elif strategy == "embedding_top_k":
        if k is None:
            k = 3
        sess, ids = topk_chronological(item_raw, hybrid_item, k)
        return conv_text(sess, ids)
    else:
        return conv_text(item_raw["haystack_sessions"], item_raw["haystack_session_ids"])


def score_answer(text, gold):
    if not text:
        return 0.0
    return 1.0 if gold.lower() in text.lower() else 0.0


# --------- Strategies ---------

def strat_naive_big(item, hybrid):
    """Always Granite 8B + full context."""
    ctx = conv_text(item["haystack_sessions"], item["haystack_session_ids"])
    ans = call_answerer("ibm-granite/granite-4.1-8b", ctx, item["question"])
    s = score_answer(ans.text, item["answer"])
    return {"strategy": "naive_big", "model_chain": ["ibm-granite/granite-4.1-8b"],
            "score": s, "cost_usd": ans.cost_usd, "latency_ms": ans.latency_ms,
            "n_attempts": 1, "confidence": ans.confidence,
            "answer_text": (ans.text or "")[:200]}


def strat_naive_small(item, hybrid):
    """Always Granite Micro + top-3 retrieval."""
    sess, ids = topk_chronological(item, hybrid, 3)
    ctx = conv_text(sess, ids)
    ans = call_answerer("ibm-granite/granite-4.0-h-micro", ctx, item["question"])
    s = score_answer(ans.text, item["answer"])
    return {"strategy": "naive_small", "model_chain": ["ibm-granite/granite-4.0-h-micro"],
            "score": s, "cost_usd": ans.cost_usd, "latency_ms": ans.latency_ms,
            "n_attempts": 1, "confidence": ans.confidence,
            "answer_text": (ans.text or "")[:200]}


_pipeline_no_escalate = None
_pipeline_escalate = None


def get_pipelines():
    global _pipeline_no_escalate, _pipeline_escalate
    if _pipeline_no_escalate is None:
        _pipeline_no_escalate = DESiPipeline(max_attempts=1)
        _pipeline_escalate = DESiPipeline(max_attempts=2, escalate_on=("low", "unknown"))
    return _pipeline_no_escalate, _pipeline_escalate


def strat_desi_v02(item, hybrid):
    """DESi v0.2: classify -> route, no escalation."""
    p, _ = get_pipelines()
    builder = lambda strat, k: build_haystack(item, hybrid, strat, k)
    res = p.run(item["question"], builder, accuracy_target=0.5)
    if res.refused or not res.final_answer:
        return {"strategy": "desi_v0_2", "model_chain": ["REFUSED"],
                "score": 0.0, "cost_usd": res.total_cost_usd,
                "latency_ms": res.total_latency_ms, "n_attempts": 0,
                "confidence": "n/a", "task_class": res.task_class,
                "answer_text": "(refused)"}
    s = score_answer(res.final_answer.text, item["answer"])
    return {"strategy": "desi_v0_2", "task_class": res.task_class,
            "model_chain": [a.decision.model for a in res.attempts],
            "score": s, "cost_usd": res.total_cost_usd, "latency_ms": res.total_latency_ms,
            "n_attempts": len(res.attempts),
            "confidence": res.final_answer.confidence,
            "answer_text": (res.final_answer.text or "")[:200]}


def strat_desi_v03(item, hybrid):
    """DESi v0.3: with confidence-based escalation."""
    _, p = get_pipelines()
    builder = lambda strat, k: build_haystack(item, hybrid, strat, k)
    res = p.run(item["question"], builder, accuracy_target=0.5)
    if res.refused or not res.final_answer:
        return {"strategy": "desi_v0_3", "model_chain": ["REFUSED"],
                "score": 0.0, "cost_usd": res.total_cost_usd,
                "latency_ms": res.total_latency_ms, "n_attempts": 0,
                "confidence": "n/a", "task_class": res.task_class,
                "answer_text": "(refused)", "escalated": False}
    s = score_answer(res.final_answer.text, item["answer"])
    return {"strategy": "desi_v0_3", "task_class": res.task_class,
            "model_chain": [a.decision.model for a in res.attempts],
            "score": s, "cost_usd": res.total_cost_usd, "latency_ms": res.total_latency_ms,
            "n_attempts": len(res.attempts),
            "confidence": res.final_answer.confidence,
            "escalated": res.escalated,
            "answer_text": (res.final_answer.text or "")[:200]}


STRATEGIES = [
    ("naive_big", strat_naive_big),
    ("naive_small", strat_naive_small),
    ("desi_v0_2", strat_desi_v02),
    ("desi_v0_3", strat_desi_v03),
]


def main():
    print("Loading dataset + hybrid items...", flush=True)
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid_items = [json.loads(p.read_text()) for p in sorted(_HYBRID.glob("*.json"))]
    # Scorable = exclude single-session-preference
    pairs = []
    for h in hybrid_items:
        qid = h["question_id"]
        if qid not in by_qid:
            continue
        if by_qid[qid].get("question_type") == "single-session-preference":
            continue
        pairs.append((by_qid[qid], h))
    print(f"  {len(pairs)} scorable items", flush=True)

    # Warm up classifier + embedding so first parallel worker doesn't race
    embed().encode(["warmup"])
    DESiPipeline().router._get_classifier().classify("warmup")

    all_results = []

    def run_for_item(item, hybrid):
        out = {"qid": item["question_id"], "question_type": item["question_type"],
               "question": item["question"], "gold": item["answer"]}
        for name, fn in STRATEGIES:
            try:
                r = fn(item, hybrid)
            except Exception as e:
                r = {"strategy": name, "error": f"{type(e).__name__}: {e}",
                     "score": 0.0, "cost_usd": 0.0, "latency_ms": 0,
                     "n_attempts": 0, "confidence": "error",
                     "model_chain": [], "answer_text": ""}
            out[name] = r
        return out

    print(f"\nRunning {len(pairs)} items x {len(STRATEGIES)} strategies = "
          f"{len(pairs)*len(STRATEGIES)} answerer calls (plus 2x classifier per item)",
          flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_for_item, item, hybrid): item["question_id"]
                for item, hybrid in pairs}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                r = fut.result()
                all_results.append(r)
                done += 1
                if done % 5 == 0 or done <= 2:
                    print(f"  [{done}/{len(pairs)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {type(e).__name__}: {e}", flush=True)

    # Per-strategy summary
    print("\n" + "=" * 78)
    print("PER-STRATEGY SUMMARY")
    print("=" * 78)
    print(f'{"strategy":<14} {"acc":>7} {"mean_cost":>12} {"total_cost":>11} '
          f'{"mean_lat":>10} {"escalation_rate":>16}')
    print("-" * 78)
    summary = {}
    for name, _ in STRATEGIES:
        scores = [r[name]["score"] for r in all_results]
        costs = [r[name]["cost_usd"] for r in all_results]
        lats = [r[name]["latency_ms"] for r in all_results]
        escalated = sum(1 for r in all_results if r[name].get("escalated"))
        acc = st.mean(scores)
        summary[name] = {
            "accuracy": round(acc, 3),
            "mean_cost_usd": round(st.mean(costs), 6),
            "total_cost_usd": round(sum(costs), 4),
            "mean_latency_ms": round(st.mean(lats)),
            "total_latency_ms": sum(lats),
            "n_escalated": escalated,
            "escalation_rate": round(escalated / len(all_results), 3),
            "cost_per_correct": round(sum(costs) / max(1, sum(scores)), 6) if sum(scores) > 0 else None,
        }
        print(f'{name:<14} {acc:>7.3f} ${st.mean(costs):>10.6f} ${sum(costs):>9.4f} '
              f'{st.mean(lats)/1000:>8.1f}s {escalated:>5}/{len(all_results):<3} '
              f'({escalated/len(all_results):.0%})')

    print()
    print("Cost-per-correct-answer:")
    for name, s in summary.items():
        cpc = s["cost_per_correct"]
        print(f'  {name:<14} ${cpc:.5f}/correct' if cpc else f'  {name:<14} (no correct answers)')

    # Save
    out_path = _OUT / "summary.json"
    out_path.write_text(json.dumps({"N": len(all_results), "by_strategy": summary,
                                     "per_item": all_results}, indent=2,
                                    default=str), encoding="utf-8")
    print(f'\nSummary written to {out_path}')


if __name__ == "__main__":
    main()
