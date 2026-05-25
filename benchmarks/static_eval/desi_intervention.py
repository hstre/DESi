#!/usr/bin/env python3
"""First real DESi intervention layer for the static-eval pipeline.

Up to now DESi only *observed* (replay hash, claim id, run_desi metrics) without
changing the answer. `apply_desi_intervention` is the first step where DESi
*acts*: after the LLM call but before the answer is finalised, it decides whether
to accept, abstain, or reject the answer, and replaces blocked answers with an
explicit ``UNKNOWN`` while preserving the original as ``raw_model_answer``.

Decision rules (most-specific first):
  - finish_reason == "length"                  -> abstain_truncated
  - reasoning_tokens > reasoning_cutoff         -> abstain_inefficient
  - answer empty or "UNKNOWN"                   -> abstain
  - answer strongly matches a known incorrect   -> reject_known_false
  - answer strongly matches a known correct     -> accept_supported
  - otherwise                                   -> accept_uncertain

Blocked decisions (answer replaced with UNKNOWN): abstain, abstain_truncated,
abstain_inefficient, reject_known_false. The matcher mirrors the report's
overlap heuristic so that "reject_known_false" lines up with the report's
"hallucination-suspect" label.
"""
from __future__ import annotations

BLOCKING_DECISIONS = frozenset({
    "abstain", "abstain_truncated", "abstain_inefficient", "reject_known_false",
})


def _norm(s: object) -> str:
    out = "".join(c if c.isalnum() or c.isspace() else " " for c in str(s).lower())
    return " ".join(out.split())


def strong_match(answer: str, candidates: list) -> bool:
    """Exact or containment match against any candidate (same as the report)."""
    a = _norm(answer)
    if not a:
        return False
    for c in candidates or []:
        cn = _norm(c)
        if cn and (a == cn or cn in a or a in cn):
            return True
    return False


def decide(answer: str, finish_reason: str | None, reasoning_tokens: int | None,
           reasoning_cutoff: int | None, correct: list, incorrect: list
           ) -> tuple[str, str]:
    a = answer.strip()
    if finish_reason == "length":
        return ("abstain_truncated",
                "finish_reason=length: reasoning was truncated, answer unreliable")
    if (reasoning_tokens is not None and reasoning_cutoff is not None
            and reasoning_tokens > reasoning_cutoff):
        return ("abstain_inefficient",
                f"reasoning_tokens {reasoning_tokens} exceeds cutoff {reasoning_cutoff}")
    if a == "" or a.upper() == "UNKNOWN":
        return "abstain", "model returned an empty or UNKNOWN answer"
    if strong_match(answer, incorrect):
        return ("reject_known_false",
                "answer strongly matches a known-incorrect TruthfulQA answer")
    if strong_match(answer, correct):
        return ("accept_supported",
                "answer strongly matches a known-correct TruthfulQA answer")
    return "accept_uncertain", "no strong match to a known correct or incorrect answer"


def apply_desi_intervention(record: dict, task: dict,
                            *, reasoning_cutoff: int | None = None) -> dict:
    """Apply the DESi intervention to a run record. Returns a new record.

    Reads the answer + call signals from ``record`` (and ``task`` for the gold
    answer lists), decides, and — for blocking decisions — replaces
    ``model_answer`` with ``UNKNOWN`` while keeping the original in
    ``raw_model_answer``. Adds intervention fields to ``desi_metadata``.
    """
    se = record.get("static_eval", {}) or {}
    meta = dict(record.get("desi_metadata") or {})
    task = task or {}

    answer = record.get("model_answer", "") or ""
    finish_reason = se.get("finish_reason") or meta.get("finish_reason")
    reasoning_tokens = se.get("reasoning_tokens")
    if reasoning_tokens is None:
        reasoning_tokens = (meta.get("usage") or {}).get("reasoning_tokens")
    cutoff = reasoning_cutoff if reasoning_cutoff is not None else se.get("reasoning_cutoff")
    correct = task.get("correct_answers") or se.get("correct_answers") or []
    incorrect = task.get("incorrect_answers") or se.get("incorrect_answers") or []

    decision, reason = decide(answer, finish_reason, reasoning_tokens, cutoff,
                              correct, incorrect)

    out = dict(record)
    out["raw_model_answer"] = answer
    out["model_answer"] = "UNKNOWN" if decision in BLOCKING_DECISIONS else answer

    meta["intervention_enabled"] = True
    meta["intervention_decision"] = decision
    meta["intervention_reason"] = reason
    meta["raw_model_answer_preserved"] = True
    out["desi_metadata"] = meta
    return out


__all__ = ["BLOCKING_DECISIONS", "apply_desi_intervention", "decide", "strong_match"]
