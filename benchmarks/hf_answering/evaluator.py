"""Benchmark evaluator for boolean QA (PERIPHERAL).

Exact-match boolean scoring with a confusion matrix. Deterministic: one parse
per answer, no repair heuristics, no retries. 'Positive' = True.
"""
from __future__ import annotations

import time

from schemas import Confusion, EvalResult, ModelAnswer, QAExample

# The single, fixed prompt used for every example (no per-example tuning).
BOOLQ_PROMPT = (
    "Answer the question with exactly one word: yes or no.\n\n"
    "Passage: {passage}\n\nQuestion: {question}\n\nAnswer:"
)

_TRUE = {"yes", "true", "y", "1"}
_FALSE = {"no", "false", "n", "0"}


def build_prompt(ex: QAExample) -> str:
    return BOOLQ_PROMPT.format(passage=ex.passage, question=ex.question)


def parse_bool(text: str) -> bool | None:
    """Parse a boolean from the model's first informative token. No repair: if
    the answer is not clearly yes/no, return None (counted as unparsed)."""
    if not text:
        return None
    first = text.strip().lower().lstrip("\"'`*-.: ").split()
    for tok in first[:3]:
        t = tok.strip(".,!?:;\"'`*()").lower()
        if t in _TRUE:
            return True
        if t in _FALSE:
            return False
    return None


def evaluate(
    examples: list[QAExample],
    answers: list[ModelAnswer],
    *,
    model: str,
    elapsed_s: float,
    price: tuple[float, float] | None = None,
) -> EvalResult:
    by_id = {a.id: a for a in answers}
    tp = tn = fp = fn = 0
    answered = unparsed = errors = 0
    pt = ct = 0
    for ex in examples:
        a = by_id.get(ex.id)
        if a is None or a.error:
            errors += 1
            continue
        pt += a.prompt_tokens
        ct += a.completion_tokens
        if a.parsed is None:
            unparsed += 1
            continue
        answered += 1
        if a.parsed and ex.gold:
            tp += 1
        elif (not a.parsed) and (not ex.gold):
            tn += 1
        elif a.parsed and (not ex.gold):
            fp += 1
        else:
            fn += 1
    accuracy = ((tp + tn) / answered) if answered else None
    est_cost = (pt * price[0] + ct * price[1]) if price else None
    return EvalResult(
        model=model, n=len(examples), answered=answered, unparsed=unparsed,
        errors=errors, accuracy=accuracy,
        confusion=Confusion(tp=tp, tn=tn, fp=fp, fn=fn),
        elapsed_s=round(elapsed_s, 2), est_cost_usd=est_cost,
    )


def answer_all(examples: list[QAExample], port) -> tuple[list[ModelAnswer], float]:
    """One deterministic pass: call the port once per example. No retries, no
    repair. A per-example failure is recorded as an error, not retried."""
    out: list[ModelAnswer] = []
    t0 = time.time()
    for ex in examples:
        prompt = build_prompt(ex)
        try:
            text, pt, ct = port.answer(prompt)
            out.append(ModelAnswer(ex.id, text, parse_bool(text), pt, ct, None))
        except Exception as exc:  # recorded, never retried/repaired
            out.append(ModelAnswer(ex.id, "", None, 0, 0, repr(exc)[:160]))
    return out, time.time() - t0


__all__ = ["BOOLQ_PROMPT", "answer_all", "build_prompt", "evaluate", "parse_bool"]
