"""Mixed-Workload Live Benchmark — the REAL test of DESi's routing thesis.

15 items mixed across 3 task classes (5 each):
  - 5x memory_recall (LongMemEval-S, multi-session conversation)
  - 5x code_audit (planted-bug code review)
  - 5x scientific_claim (SciFact verification)

4 strategies:
  1. naive_big:      Granite 4.1 8B + raw context (always)
  2. naive_small_r:  Granite Micro + top-3 retrieval (always)  — wins on memory, fails on code
  3. naive_small_x:  Granite Micro + raw context (always)      — wins on code, suboptimal on memory
  4. desi_v0_3:      classify -> route -> escalate (auto-adapts per task)

For each item: each strategy produces an answer; per-task scoring; aggregate per strategy.

The DESi thesis: on heterogeneous workloads, no fixed strategy is best for all task
classes. DESi's auto-routing should be Pareto-optimal: matches naive_small_r on
memory tasks AND naive_small_x on code tasks, in one pipeline.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import statistics as st
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from desi.pipeline import DESiPipeline
from desi.answerer import answer as call_answerer
from code_review_bugs import BUGS, DISTRACTORS

_OUT = _HERE / "results" / "minimaltest_mixed_workload"
_OUT.mkdir(parents=True, exist_ok=True)
_HYBRID = _HERE / "results" / "minimaltest_hybrid" / "items"
_PA_ORIG = _HERE / "results" / "minimaltest_paper_audit" / "items"
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"
SCIFACT = _HERE / "data" / "scifact" / "data"

SEED = 42
PARALLELISM = 4

_EMBED = None


def embed():
    global _EMBED
    if _EMBED is None:
        _EMBED = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED


# ---------- Item assembly (3 task classes -> uniform schema) ----------

def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def assemble_memory_recall():
    """5 LongMemEval items + their existing top-10 retrievals."""
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid_items = sorted(_HYBRID.glob("*.json"))
    pool = []
    for p in hybrid_items:
        h = json.loads(p.read_text())
        qid = h["question_id"]
        if qid not in by_qid:
            continue
        if by_qid[qid].get("question_type") == "single-session-preference":
            continue
        pool.append((by_qid[qid], h))
    rng = random.Random(SEED)
    chosen = rng.sample(pool, 5)
    items = []
    for raw, h in chosen:
        # chunks = each session as a chunk; chunk_id = session_id
        sessions = raw["haystack_sessions"]
        sids = raw["haystack_session_ids"]
        chunks = [{"id": sid, "text": session_text(s)} for s, sid in zip(sessions, sids)]
        # gold_evidence_ids = sessions that contain the answer
        items.append({
            "task_class": "memory_recall",
            "item_id": "mr_" + raw["question_id"],
            "question": raw["question"],
            "gold_answer": raw["answer"],
            "chunks": chunks,
            "gold_evidence_ids": list(raw["answer_session_ids"]),
        })
    return items


def assemble_code_audit():
    """5 planted-bug cases. Chunks = the 9 modules (1 buggy + 8 distractors)."""
    rng = random.Random(SEED)
    chosen_bugs = rng.sample(BUGS, 5)
    items = []
    for b in chosen_bugs:
        chunks = [{"id": f"{b['function']}.py", "text": b["buggy_source"]}]
        for name, src in DISTRACTORS:
            chunks.append({"id": name, "text": src})
        items.append({
            "task_class": "code_audit",
            "item_id": "ca_" + b["id"],
            "question": ("Audit the following Python code. Find any bugs, security "
                         "issues, or subtle correctness problems. Name the function "
                         "and explain what is wrong."),
            "gold_answer": b["function"],   # function name must appear
            "code_audit_function": b["function"],
            "code_audit_must_contain": b["must_contain"],
            "chunks": chunks,
            "gold_evidence_ids": [f"{b['function']}.py"],
        })
    return items


def assemble_scientific_claim():
    """5 SciFact claims. Chunks = the 9 abstracts (1 cited + 8 distractors)."""
    pa_files = sorted(_PA_ORIG.glob("*.json"))
    pa_items = [json.loads(p.read_text()) for p in pa_files]
    # Need corpus to render abstracts
    corpus = {d["doc_id"]: d
              for d in (json.loads(l) for l in open(SCIFACT / "corpus.jsonl"))}
    rng = random.Random(SEED)
    rng.shuffle(pa_items)
    items = []
    for pa in pa_items:
        if len(items) >= 5:
            break
        haystack_ids = pa["haystack_doc_ids"]
        chunks = []
        for did in haystack_ids:
            if did not in corpus:
                continue
            doc = corpus[did]
            body = " ".join(doc.get("abstract") or []) if isinstance(doc.get("abstract"), list) else doc.get("abstract", "")
            chunks.append({"id": str(did),
                           "text": f"[doc_id {did}] Title: {doc.get('title','(no title)')}\nAbstract: {body}"})
        if len(chunks) < 5:
            continue
        items.append({
            "task_class": "scientific_claim",
            "item_id": "sc_" + str(pa["claim_id"]),
            "question": (f"{pa['claim_text']}\n\n"
                         "Respond with VERDICT: SUPPORT | CONTRADICT | NEI on the "
                         "first line, then 1-2 sentences."),
            "gold_answer": pa["gold_label"],
            "chunks": chunks,
            "gold_evidence_ids": [str(pa["cited_doc_id"])],
        })
    return items


# ---------- Context builders ----------

def build_context(chunks, strategy: str, k: int | None, question: str):
    if strategy == "raw_full":
        # Concatenate everything
        if not chunks:
            return ""
        sep = "\n\n=== "
        return "=== " + f"{sep}".join(f"{c['id']} ===\n{c['text']}" for c in chunks)
    elif strategy == "embedding_top_k":
        if k is None:
            k = 3
        em = embed()
        texts = [c["text"] for c in chunks]
        q_emb = em.encode([question], normalize_embeddings=True)
        c_embs = em.encode(texts, normalize_embeddings=True, batch_size=8, show_progress_bar=False)
        sims = (c_embs @ q_emb.T).ravel()
        top = np.argsort(-sims)[:k].tolist()
        # Preserve original order (chronology proxy)
        top_sorted = sorted(top)
        chosen = [chunks[i] for i in top_sorted]
        sep = "\n\n=== "
        return "=== " + f"{sep}".join(f"{c['id']} ===\n{c['text']}" for c in chosen)
    else:
        return ""


# ---------- Per-task scoring ----------

_VERDICT_RE = re.compile(r"VERDICT:\s*(SUPPORT|CONTRADICT|NEI)", re.IGNORECASE)


def score_answer(item, ans_text):
    if not ans_text:
        return 0.0
    tc = item["task_class"]
    if tc == "memory_recall":
        return 1.0 if item["gold_answer"].lower() in ans_text.lower() else 0.0
    elif tc == "code_audit":
        text_l = ans_text.lower()
        fn = item["code_audit_function"].lower()
        loc = fn in text_l
        desc = any(m.lower() in text_l for m in item["code_audit_must_contain"])
        if loc and desc:
            return 1.0
        elif loc or desc:
            return 0.5
        else:
            return 0.0
    elif tc == "scientific_claim":
        m = _VERDICT_RE.search(ans_text)
        if not m:
            for label in ("CONTRADICT", "SUPPORT", "NEI"):
                if re.search(rf"\b{label}\b", ans_text, re.IGNORECASE):
                    return 1.0 if label == item["gold_answer"] else 0.0
            return 0.0
        return 1.0 if m.group(1).upper() == item["gold_answer"] else 0.0
    return 0.0


# ---------- Strategies ----------

def strat_naive_big(item):
    ctx = build_context(item["chunks"], "raw_full", None, item["question"])
    ans = call_answerer("ibm-granite/granite-4.1-8b", ctx, item["question"])
    return {"strategy": "naive_big", "score": score_answer(item, ans.text),
            "cost_usd": ans.cost_usd, "latency_ms": ans.latency_ms,
            "model_chain": ["ibm-granite/granite-4.1-8b"],
            "confidence": ans.confidence, "n_attempts": 1,
            "answer_text": (ans.text or "")[:250]}


def strat_naive_small_retr(item):
    ctx = build_context(item["chunks"], "embedding_top_k", 3, item["question"])
    ans = call_answerer("ibm-granite/granite-4.0-h-micro", ctx, item["question"])
    return {"strategy": "naive_small_r", "score": score_answer(item, ans.text),
            "cost_usd": ans.cost_usd, "latency_ms": ans.latency_ms,
            "model_chain": ["ibm-granite/granite-4.0-h-micro"],
            "confidence": ans.confidence, "n_attempts": 1,
            "answer_text": (ans.text or "")[:250]}


def strat_naive_small_raw(item):
    ctx = build_context(item["chunks"], "raw_full", None, item["question"])
    ans = call_answerer("ibm-granite/granite-4.0-h-micro", ctx, item["question"])
    return {"strategy": "naive_small_x", "score": score_answer(item, ans.text),
            "cost_usd": ans.cost_usd, "latency_ms": ans.latency_ms,
            "model_chain": ["ibm-granite/granite-4.0-h-micro"],
            "confidence": ans.confidence, "n_attempts": 1,
            "answer_text": (ans.text or "")[:250]}


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = DESiPipeline(max_attempts=2, escalate_on=("low", "unknown"))
    return _pipeline


def strat_desi(item):
    p = get_pipeline()
    builder = lambda strategy, k: build_context(item["chunks"], strategy, k, item["question"])
    res = p.run(item["question"], builder, accuracy_target=0.5)
    if res.refused or not res.final_answer:
        return {"strategy": "desi_v0_3", "score": 0.0,
                "cost_usd": res.total_cost_usd, "latency_ms": res.total_latency_ms,
                "model_chain": ["REFUSED"], "confidence": "n/a", "n_attempts": 0,
                "task_class_predicted": res.task_class, "escalated": res.escalated,
                "answer_text": "(refused)"}
    s = score_answer(item, res.final_answer.text)
    return {"strategy": "desi_v0_3", "score": s,
            "cost_usd": res.total_cost_usd, "latency_ms": res.total_latency_ms,
            "model_chain": [a.decision.model for a in res.attempts],
            "task_class_predicted": res.task_class,
            "confidence": res.final_answer.confidence,
            "n_attempts": len(res.attempts), "escalated": res.escalated,
            "answer_text": (res.final_answer.text or "")[:250]}


STRATEGIES = [
    ("naive_big", strat_naive_big),
    ("naive_small_r", strat_naive_small_retr),
    ("naive_small_x", strat_naive_small_raw),
    ("desi_v0_3", strat_desi),
]


def main():
    print("Assembling mixed workload...", flush=True)
    items = (assemble_memory_recall() + assemble_code_audit() + assemble_scientific_claim())
    print(f"  {len(items)} items: ", flush=True)
    by_tc = defaultdict(int)
    for it in items:
        by_tc[it["task_class"]] += 1
    for tc, n in sorted(by_tc.items()):
        print(f"    {tc}: {n}", flush=True)

    embed().encode(["warmup"])
    get_pipeline().router._get_classifier().classify("warmup")

    def run_one(item):
        out = {"item_id": item["item_id"], "task_class": item["task_class"],
               "question": item["question"][:200], "gold": item["gold_answer"]}
        for name, fn in STRATEGIES:
            try:
                out[name] = fn(item)
            except Exception as e:
                out[name] = {"strategy": name, "score": 0.0, "cost_usd": 0.0,
                             "latency_ms": 0, "model_chain": [],
                             "confidence": "error", "n_attempts": 0,
                             "error": f"{type(e).__name__}: {e}",
                             "answer_text": ""}
        return out

    print(f"\nRunning {len(items)} items x {len(STRATEGIES)} strategies = "
          f"{len(items)*len(STRATEGIES)} answerer calls...", flush=True)
    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_one, it): it["item_id"] for it in items}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                r = fut.result()
                results.append(r)
                done += 1
                if done % 3 == 0:
                    print(f"  [{done}/{len(items)}] {iid}", flush=True)
            except Exception as e:
                print(f"  ERROR {iid}: {type(e).__name__}: {e}", flush=True)

    # --- Per-strategy aggregate, then per-task-class breakdown ---
    print("\n" + "=" * 84)
    print("MIXED-WORKLOAD RESULTS (5 memory_recall + 5 code_audit + 5 scientific_claim = 15)")
    print("=" * 84)
    print(f'{"strategy":<16} {"memory":>9} {"code":>9} {"science":>9} {"overall":>9} '
          f'{"cost":>10} {"latency":>10}')
    print("-" * 84)
    summary = {"N": len(results), "by_strategy": {}}
    for name, _ in STRATEGIES:
        per_tc = defaultdict(list)
        for r in results:
            per_tc[r["task_class"]].append(r[name]["score"])
        overall_scores = [r[name]["score"] for r in results]
        costs = [r[name]["cost_usd"] for r in results]
        lats = [r[name]["latency_ms"] for r in results]
        m = st.mean(per_tc.get("memory_recall", [0]))
        c = st.mean(per_tc.get("code_audit", [0]))
        s = st.mean(per_tc.get("scientific_claim", [0]))
        ov = st.mean(overall_scores)
        print(f'{name:<16} {m:>9.2f} {c:>9.2f} {s:>9.2f} {ov:>9.3f} '
              f'${sum(costs):>8.4f} {st.mean(lats)/1000:>8.1f}s')
        summary["by_strategy"][name] = {
            "memory_recall": round(m, 3),
            "code_audit": round(c, 3),
            "scientific_claim": round(s, 3),
            "overall": round(ov, 3),
            "total_cost_usd": round(sum(costs), 4),
            "mean_latency_ms": round(st.mean(lats)),
        }

    # Desi-specific: routing decisions per task class
    print("\nDESi v0.3 routing breakdown:")
    classification_correct = 0
    escalated_n = 0
    for r in results:
        d = r["desi_v0_3"]
        pred = d.get("task_class_predicted", "?")
        actual = r["task_class"]
        ok = "✓" if pred == actual else "✗"
        if pred == actual:
            classification_correct += 1
        if d.get("escalated"):
            escalated_n += 1
        chain = " -> ".join(m.split("/")[-1] for m in d.get("model_chain", []))
        print(f'  [{actual:<18}] classified as {pred:<18} {ok}  chain: {chain}')
    print(f'\n  Classification accuracy: {classification_correct}/{len(results)} = '
          f'{classification_correct/len(results):.0%}')
    print(f'  Escalation rate: {escalated_n}/{len(results)} = {escalated_n/len(results):.0%}')

    summary["desi_classification_accuracy"] = round(classification_correct / len(results), 3)
    summary["desi_escalation_rate"] = round(escalated_n / len(results), 3)
    summary["per_item"] = results

    out_path = _OUT / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nSummary written to {out_path}")


if __name__ == "__main__":
    main()
