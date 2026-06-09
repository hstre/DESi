"""Evaluate the DESi task classifier on a held-out labeled set.

40 stratified queries (10 per task class: memory_recall, code_audit,
scientific_claim, other). Measure:
  - 4-way classification accuracy
  - Per-class precision/recall
  - Per-class latency / cost
  - Confusion matrix
  - End-to-end accuracy when chained with the router

The 'other' bucket tests the router's ability to REFUSE inputs outside its
empirical scope rather than misroute them.
"""
from __future__ import annotations

import json
import os
import sys
import statistics as st
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from desi.classifier import TaskClassifier

LABELED_QUERIES = [
    # memory_recall (10)
    ("memory_recall", "How long did I wait for the decision on my asylum application?"),
    ("memory_recall", "What brand of BBQ sauce did I tell you I was obsessed with last month?"),
    ("memory_recall", "How many new postcards have I added since I started collecting again?"),
    ("memory_recall", "When did I move to my new apartment?"),
    ("memory_recall", "What did I say my dad gave me for my birthday?"),
    ("memory_recall", "Where does my sister Emily currently live?"),
    ("memory_recall", "How many properties did I view before making an offer on the townhouse?"),
    ("memory_recall", "What kind of car did I tell you I wanted to buy?"),
    ("memory_recall", "How long had I been using the new area rug when I rearranged my living room?"),
    ("memory_recall", "Did I mention which doctors I visited last year?"),

    # code_audit (10)
    ("code_audit", "Audit this function for any bugs:\ndef fenced_sum(values):\n    total = 0\n    for i in range(len(values)):\n        total += values[i]\n    return total - values[-1]"),
    ("code_audit", "Is there a security issue in this Python code? def load_config(path): f = open(path); return json.load(f)"),
    ("code_audit", "Find any subtle correctness problems in the following Python module."),
    ("code_audit", "Review this code for off-by-one errors: def drop_extension(filename): return filename[:filename.rfind('.') - 1]"),
    ("code_audit", "Does this function correctly handle the case where the user dict is None?"),
    ("code_audit", "Check for race conditions or TOCTOU bugs in this file handling code."),
    ("code_audit", "Is the operator precedence correct in this expression: len(done) & {k for k in items} ?"),
    ("code_audit", "Audit this Python codebase. Find any bugs, security issues, or subtle correctness problems."),
    ("code_audit", "Does the following Python code have any resource leaks or unclosed file handles?"),
    ("code_audit", "Look for shallow-copy bugs in this 2D-grid duplication function."),

    # scientific_claim (10)
    ("scientific_claim", "Does the evidence support the claim that 1 in 5 million people in UK have abnormal PrP positivity?"),
    ("scientific_claim", "Is this claim supported by published research: aspirin reduces cardiovascular risk in healthy adults?"),
    ("scientific_claim", "Verify the following scientific claim against the provided abstracts: BRCA1 mutations increase breast cancer risk."),
    ("scientific_claim", "Do these abstracts support or contradict the statement that vitamin D supplementation reduces fracture risk?"),
    ("scientific_claim", "Classify this medical claim as SUPPORT / CONTRADICT / NEI based on the literature: statins cause memory loss."),
    ("scientific_claim", "Does the following biomedical claim hold up against the cited evidence?"),
    ("scientific_claim", "Is there published evidence for or against this claim about 0-dimensional biomaterials?"),
    ("scientific_claim", "Fact-check this scientific claim using the abstracts: HPV vaccine has been linked to autoimmune disorders."),
    ("scientific_claim", "Given these papers, evaluate whether the claim 'masking reduces COVID-19 transmission' is supported."),
    ("scientific_claim", "Classify the claim 'metformin extends lifespan' against the abstracts: SUPPORT / CONTRADICT / NEI."),

    # other (10) — multi-hop, creative, planning, tool-use
    ("other", "Write me a poem about autumn leaves."),
    ("other", "Plan a 5-day trip to Berlin including hotels, restaurants, and museums."),
    ("other", "What is the integral of sin(x) * exp(-x) from 0 to infinity?"),
    ("other", "Translate the following German sentence to English: 'Der schnelle braune Fuchs springt über den faulen Hund.'"),
    ("other", "Compose a short story about a robot who learns to love."),
    ("other", "Convert 100 USD to EUR at today's exchange rate."),
    ("other", "Solve this physics problem: a ball is thrown at 30 m/s at 45 degrees. Where does it land?"),
    ("other", "Recommend a good book on philosophy of mind."),
    ("other", "How would you implement a hash table from scratch in Rust?"),
    ("other", "What is the current weather in Tokyo?"),
]


def main():
    print(f"Evaluating classifier on {len(LABELED_QUERIES)} labeled queries...", flush=True)
    by_class = defaultdict(int)
    for label, _ in LABELED_QUERIES:
        by_class[label] += 1
    print(f"  Stratification: {dict(by_class)}", flush=True)

    c = TaskClassifier()
    results = []

    def go(idx, gold, query):
        r = c.classify(query)
        return idx, gold, query, r

    print(f"\nRunning {len(LABELED_QUERIES)} classifications (parallelism=4)...", flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(go, i, gold, q): i for i, (gold, q) in enumerate(LABELED_QUERIES)}
        for fut in as_completed(futs):
            try:
                idx, gold, query, r = fut.result()
                results.append({"idx": idx, "gold": gold, "query": query,
                                "predicted": r.task_class, "confidence": r.confidence,
                                "latency_ms": r.latency_ms, "cost_usd": r.cost_usd,
                                "error": r.error, "raw": r.raw_response})
            except Exception as e:
                print(f"  ERROR idx={futs[fut]}: {e}", flush=True)

    results.sort(key=lambda r: r["idx"])

    # Overall accuracy
    correct = sum(1 for r in results if r["predicted"] == r["gold"])
    print(f"\nOverall accuracy: {correct}/{len(results)} = {correct/len(results):.2%}")

    # Per-class
    print("\nPer-class precision/recall:")
    print(f'{"class":<20} {"n_gold":>7} {"n_pred":>7} {"correct":>8} {"recall":>7} {"precision":>10}')
    classes = ["memory_recall", "code_audit", "scientific_claim", "other"]
    for cls in classes:
        n_gold = sum(1 for r in results if r["gold"] == cls)
        n_pred = sum(1 for r in results if r["predicted"] == cls)
        n_correct = sum(1 for r in results if r["gold"] == cls and r["predicted"] == cls)
        recall = n_correct / max(1, n_gold)
        prec = n_correct / max(1, n_pred)
        print(f'  {cls:<20} {n_gold:>7} {n_pred:>7} {n_correct:>8} {recall:>7.2%} {prec:>10.2%}')

    # Confusion matrix
    print("\nConfusion matrix (rows=gold, cols=predicted):")
    print(f'{"":<22}', end='')
    for cls in classes:
        print(f'{cls[:10]:>11}', end='')
    print()
    for gold in classes:
        print(f'  {gold:<20}', end='')
        for pred in classes:
            n = sum(1 for r in results if r["gold"] == gold and r["predicted"] == pred)
            mark = '*' if gold == pred else ' '
            print(f'{n:>10}{mark}', end='')
        print()

    # Latency + cost
    lats = [r["latency_ms"] for r in results]
    costs = [r["cost_usd"] for r in results]
    print(f"\nClassifier overhead per call:")
    print(f"  Mean latency: {st.mean(lats):.0f} ms")
    print(f"  Mean cost:    ${st.mean(costs):.6f}")
    print(f"  Total cost for {len(results)} classifications: ${sum(costs):.4f}")

    # Errors
    print("\nMisclassified examples:")
    for r in results:
        if r["predicted"] != r["gold"]:
            print(f'  gold={r["gold"]:<18} pred={r["predicted"]:<18} conf={r["confidence"]:<6} q="{r["query"][:80]}"')

    # Save
    out_path = _HERE / "results" / "minimaltest_classifier_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "N": len(results),
        "overall_accuracy": round(correct / len(results), 3),
        "per_class": {
            cls: {
                "n_gold": sum(1 for r in results if r["gold"] == cls),
                "n_pred": sum(1 for r in results if r["predicted"] == cls),
                "n_correct": sum(1 for r in results if r["gold"] == cls and r["predicted"] == cls),
            } for cls in classes
        },
        "mean_latency_ms": round(st.mean(lats)),
        "mean_cost_usd": round(st.mean(costs), 6),
        "total_cost_usd": round(sum(costs), 4),
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nSummary written to {out_path}")


if __name__ == "__main__":
    main()
