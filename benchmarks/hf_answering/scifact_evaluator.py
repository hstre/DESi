"""3-class fact-verification evaluator (PERIPHERAL) — SciFact / FEVER-style.

Verdicts: SUPPORTS / REFUTES / NOT_ENOUGH_INFO. Exact-match scoring with a 3x3
confusion matrix and class distributions. Deterministic: one fixed prompt, one
parse per answer, no retries, no answer repair, no benchmark-specific ontology.
DESi is NOT the claim reasoner — an external model port produces the verdict.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

LABELS = ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO")

VERIFY_PROMPT = (
    "You are a fact-checking classifier. Read the EVIDENCE and decide whether it "
    "SUPPORTS the CLAIM, REFUTES the CLAIM, or gives NOT_ENOUGH_INFO. Respond "
    "with exactly one label: SUPPORTS, REFUTES, or NOT_ENOUGH_INFO.\n\n"
    "CLAIM: {claim}\n\nEVIDENCE: {evidence}\n\nLabel:"
)

# fixed label parsing (synonyms only; this is parsing, not answer repair)
_SYNONYMS = {
    "SUPPORTS": ("supports", "support", "supported", "entailment", "entails", "true"),
    "REFUTES": ("refutes", "refute", "refuted", "contradicts", "contradiction",
                "contradicted", "false"),
    "NOT_ENOUGH_INFO": ("not_enough_info", "not enough info", "not enough information",
                        "nei", "neutral", "insufficient", "unknown", "not enough"),
}
# dataset gold-label normalization -> canonical LABELS
_GOLD_MAP = {
    "supports": "SUPPORTS", "support": "SUPPORTS", "entailment": "SUPPORTS",
    "refutes": "REFUTES", "contradiction": "REFUTES",
    "not enough info": "NOT_ENOUGH_INFO", "not_enough_info": "NOT_ENOUGH_INFO",
    "not enough information": "NOT_ENOUGH_INFO", "neutral": "NOT_ENOUGH_INFO",
    "nei": "NOT_ENOUGH_INFO",
}


@dataclass(frozen=True)
class VerifyExample:
    id: str
    claim: str
    evidence: str
    gold: str  # one of LABELS


@dataclass(frozen=True)
class VerifyAnswer:
    id: str
    raw_text: str
    parsed: str | None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    error: str | None = None


def normalize_gold(raw_label) -> str | None:
    if raw_label is None:
        return None
    return _GOLD_MAP.get(str(raw_label).strip().lower())


def build_prompt(ex: VerifyExample) -> str:
    return VERIFY_PROMPT.format(claim=ex.claim, evidence=ex.evidence)


def parse_label(text: str) -> str | None:
    """Pick the label whose synonym appears earliest in the response. No repair:
    if no known label token is present, return None (counted as parse failure)."""
    if not text:
        return None
    low = text.strip().lower()
    best_label, best_idx = None, len(low) + 1
    for label, syns in _SYNONYMS.items():
        for s in syns:
            idx = low.find(s)
            if idx != -1 and idx < best_idx:
                best_label, best_idx = label, idx
    return best_label


def answer_all(examples: list[VerifyExample], port) -> tuple[list[VerifyAnswer], float]:
    """One deterministic pass: one call per example, no retries, no repair."""
    out: list[VerifyAnswer] = []
    t0 = time.time()
    for ex in examples:
        try:
            text, pt, ct = port.answer(build_prompt(ex))
            out.append(VerifyAnswer(ex.id, text, parse_label(text), pt, ct, None))
        except Exception as exc:
            out.append(VerifyAnswer(ex.id, "", None, 0, 0, repr(exc)[:160]))
    return out, time.time() - t0


def evaluate(examples, answers, *, price=None) -> dict:
    by = {a.id: a for a in answers}
    confusion = {g: {p: 0 for p in LABELS} for g in LABELS}
    gold_dist = {l: 0 for l in LABELS}
    pred_dist = {l: 0 for l in LABELS}
    answered = parse_fail = errors = correct = 0
    pt = ct = 0
    for ex in examples:
        gold_dist[ex.gold] += 1
        a = by.get(ex.id)
        if a is None or a.error:
            errors += 1
            continue
        pt += a.prompt_tokens
        ct += a.completion_tokens
        if a.parsed is None:
            parse_fail += 1
            continue
        answered += 1
        pred_dist[a.parsed] += 1
        confusion[ex.gold][a.parsed] += 1
        if a.parsed == ex.gold:
            correct += 1
    accuracy = (correct / answered) if answered else None
    est_cost = (pt * price[0] + ct * price[1]) if price else None
    return {
        "n": len(examples), "answered": answered, "parse_failures": parse_fail,
        "errors": errors, "correct": correct, "accuracy": accuracy,
        "confusion": confusion, "gold_distribution": gold_dist,
        "pred_distribution": pred_dist, "est_cost_usd": est_cost,
    }


__all__ = [
    "LABELS", "VERIFY_PROMPT", "VerifyAnswer", "VerifyExample", "answer_all",
    "build_prompt", "evaluate", "normalize_gold", "parse_label",
]
