"""Measure the rule-based classifier instead of asserting it - confusion matrix included.

``policy.classify`` is a keyword heuristic, and it is the weakest link of the embeddable
router: every misroute sends a query to the wrong tool or model. In the house style ("scores
measured, not asserted") its quality must be a NUMBER with a visible error surface, not a
claim. This module carries a small, hand-labeled evaluation set (synthetic, written for this
purpose - it is an honesty floor, not an external benchmark) and prints accuracy per class
plus the full confusion matrix:

    python -m desi_router.classifier_eval

Hosts embedding the router can run the same command after extending LABELED with their own
domain's queries - or bypass the built-in classifier entirely (``DesiRouter(classifier=...)``).

Honest scope: the current patterns were tuned against this very set (a 69% baseline drove the
widening), so the shipped 100% is a pinned REGRESSION FLOOR, not a generalization claim. The
way to a real accuracy number is more labels from real usage - extend LABELED and re-run.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from desi_router.policy import classify

# (query, expected class). Deliberately includes hard negatives: phrasings that LOOK like one
# class but belong to another, and 'general' queries that must not be claimed by any tool.
LABELED: list[tuple[str, str]] = [
    # date_math
    ("How many days between 2024-01-01 and 2024-03-15?", "date_math"),
    ("What date is 90 days after 2025-06-30?", "date_math"),
    ("How many weeks from 2023-12-24 until 2024-02-01?", "date_math"),
    ("Days between 2020-02-28 and 2020-03-01, please.", "date_math"),
    # unit_conversion
    ("Convert 5 km to miles", "unit_conversion"),
    ("How many kilograms is 150 pounds?", "unit_conversion"),
    ("Convert 100 fahrenheit to celsius", "unit_conversion"),
    ("What is 3 meters in feet?", "unit_conversion"),
    # math_arithmetic
    ("What is 17 * 23?", "math_arithmetic"),
    ("Compute 12*12 - 44", "math_arithmetic"),
    ("What is (7 + 8) / 3?", "math_arithmetic"),
    ("calculate 2^10 + 5", "math_arithmetic"),
    # code_audit
    ("Review this diff for SQL injection bugs", "code_audit"),
    ("Is there a race condition in this function?", "code_audit"),
    ("Audit this pull request for memory leaks", "code_audit"),
    ("Find the off-by-one error in this loop", "code_audit"),
    # scientific_claim
    ("Does this abstract support the claim that X causes Y?", "scientific_claim"),
    ("Is the hypothesis in this paper backed by the evidence presented?", "scientific_claim"),
    ("Verify the claim that the drug reduces mortality against this study.", "scientific_claim"),
    ("Does the cited evidence contradict the paper's conclusion?", "scientific_claim"),
    # memory_recall
    ("How long did I wait for the asylum decision?", "memory_recall"),
    ("What did we discuss in the last session about my visa?", "memory_recall"),
    ("When did I first mention the housing problem?", "memory_recall"),
    ("Remind me what I said about my previous employer.", "memory_recall"),
    # general - must NOT be captured by any tool class
    ("Summarize this article about urban gardening", "general"),
    ("Write a friendly reply to this email", "general"),
    ("Translate this paragraph into French", "general"),
    ("What are good interview questions for a data engineer?", "general"),
    # hard negatives: look like one class, belong to another
    ("My meeting is on 2025-03-04 in room 12", "general"),          # ISO date, no date question
    ("The recipe needs 2 pounds of flour and 3 eggs", "general"),   # units mentioned, no conversion
    ("I paid 17 euros for 23 apples, was that a fair deal?", "general"),
    ("The study of 12 patients was published in 2024", "general"),
]


def evaluate(labeled=None) -> dict:
    """Accuracy overall + per class, and the confusion matrix (expected -> predicted -> n).
    Deterministic; pure read."""
    labeled = labeled if labeled is not None else LABELED
    confusion: dict[str, Counter] = defaultdict(Counter)
    per_class: dict[str, dict] = defaultdict(lambda: {"n": 0, "correct": 0})
    correct = 0
    for query, expected in labeled:
        got = classify(query)
        confusion[expected][got] += 1
        per_class[expected]["n"] += 1
        if got == expected:
            per_class[expected]["correct"] += 1
            correct += 1
    return {
        "n": len(labeled),
        "accuracy": round(correct / len(labeled), 4) if labeled else 0.0,
        "per_class": {k: {"n": v["n"], "accuracy": round(v["correct"] / v["n"], 4)}
                      for k, v in sorted(per_class.items())},
        "confusion": {k: dict(v) for k, v in sorted(confusion.items())},
    }


def render(result: dict) -> str:
    lines = [f"classifier eval - n={result['n']}, accuracy={result['accuracy']:.0%}", ""]
    lines.append(f"{'expected':<18} {'accuracy':<9} misroutes")
    for cls, s in result["per_class"].items():
        wrong = {k: v for k, v in result["confusion"][cls].items() if k != cls}
        mis = ", ".join(f"{k}:{v}" for k, v in sorted(wrong.items())) or "-"
        lines.append(f"{cls:<18} {s['accuracy']:<9.0%} {mis}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(evaluate()))
