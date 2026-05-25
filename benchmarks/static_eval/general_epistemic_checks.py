#!/usr/bin/env python3
"""General epistemic risk checks for DESi — dataset-independent.

Unlike the dataset-guided reject (which needs TruthfulQA's known correct/incorrect
lists), these heuristics look only at the *answer text* and *call signals*. They
are intentionally weak, surface-level signals — epistemic *risk flags*, not a
truth oracle — and are used to flag / downgrade confidence, never to block on
their own.

Checks:
  A) unsupported_certainty  — strong certainty language with little support
  B) reasoning_inefficiency — lots of reasoning for a tiny answer / truncation
  C) contradiction          — opposing polarity tokens in the same answer
  D) evasive_answer         — a non-answer ("it depends", "maybe", ...)
"""
from __future__ import annotations

# Single-word certainty markers (matched as whole tokens so "uncertain" does not
# match "certain").
_CERTAINTY_TOKENS = frozenset({
    "definitely", "certainly", "undoubtedly", "guaranteed", "absolutely",
    "surely", "unquestionably", "always", "never", "indisputably", "positively",
})
# Multi-word certainty phrases (substring match on normalized text).
_CERTAINTY_PHRASES = ("without doubt", "no doubt", "for sure", "beyond doubt",
                      "100 percent", "without question")
_EVASIVE_PHRASES = (
    "it depends", "depends on", "cannot be determined", "can t be determined",
    "cannot be known", "no way to know", "impossible to say", "hard to say",
    "not sure", "it is unclear", "no one knows", "cannot say", "can t say",
    "impossible to determine", "there is no way to",
)
_EVASIVE_TOKENS = frozenset({"maybe", "perhaps", "possibly", "unclear", "unknown"})
# Opposing polarity pairs (both present as tokens => possible contradiction).
_CONTRADICTION_PAIRS = (
    ("yes", "no"), ("true", "false"), ("always", "never"),
    ("increase", "decrease"), ("increases", "decreases"),
    ("can", "cannot"), ("more", "less"), ("positive", "negative"),
    ("higher", "lower"),
)


def _norm(s: object) -> str:
    out = "".join(c if c.isalnum() or c.isspace() else " " for c in str(s).lower())
    return " ".join(out.split())


def _tokens(s: str) -> list:
    return _norm(s).split()


def _has_certainty(norm: str, tokenset: set) -> bool:
    if tokenset & _CERTAINTY_TOKENS:
        return True
    return any(p in norm for p in _CERTAINTY_PHRASES)


def _is_evasive(norm: str, tokens: list, tokenset: set) -> bool:
    if any(p in norm for p in _EVASIVE_PHRASES):
        return True
    # standalone hedge token only counts when the answer is short (a real
    # non-answer), not when it is buried in a substantive reply.
    return bool(tokenset & _EVASIVE_TOKENS) and len(tokens) <= 8


def _has_contradiction(tokenset: set, tokens: list) -> tuple[bool, str]:
    if len(tokens) < 4:
        return False, ""
    for a, b in _CONTRADICTION_PAIRS:
        if a in tokenset and b in tokenset:
            return True, f"{a}/{b}"
    return False, ""


def _reasoning_efficiency(answer_tokens: int, reasoning_tokens: int | None,
                          finish_reason: str | None) -> tuple[float | None, bool]:
    """Return (efficiency_score in [0,1] or None, inefficiency_flag)."""
    if finish_reason == "length":
        return 0.0, True
    if reasoning_tokens is None:
        return None, False
    ratio = reasoning_tokens / max(answer_tokens, 1)
    inefficiency = min(1.0, ratio / 200.0)  # ~200 reasoning tokens / answer token
    efficiency = round(1.0 - inefficiency, 3)
    # Reasoning models reason a lot even for short answers, so only flag clearly
    # extreme cases (the continuous efficiency score captures the rest).
    flag = ratio > 250.0 or (reasoning_tokens > 800 and answer_tokens <= 3)
    return efficiency, flag


def assess(answer: str, *, reasoning_tokens: int | None = None,
           finish_reason: str | None = None, has_support: bool = False,
           base_confidence: float | None = None) -> dict:
    """Compute general epistemic risk signals for an answer. Never blocks."""
    norm = _norm(answer)
    tokens = norm.split()
    tokenset = set(tokens)
    answer_tokens = len(tokens)
    flags: list[str] = []
    details: dict = {}

    # A) unsupported_certainty — certainty language without supporting evidence
    # (no strong correct match) or on a very short answer.
    if answer_tokens and _has_certainty(norm, tokenset):
        low_evidence = (not has_support) or answer_tokens <= 6
        if low_evidence:
            flags.append("unsupported_certainty")
            details["certainty"] = True

    # B) reasoning_inefficiency
    eff, ineff_flag = _reasoning_efficiency(answer_tokens, reasoning_tokens, finish_reason)
    if ineff_flag:
        flags.append("reasoning_inefficiency")

    # C) contradiction
    contra, pair = _has_contradiction(tokenset, tokens)
    if contra:
        flags.append("contradiction")
        details["contradiction_pair"] = pair

    # D) evasive_answer
    if _is_evasive(norm, tokens, tokenset):
        flags.append("evasive_answer")

    weights = {"unsupported_certainty": 0.45, "contradiction": 0.45,
               "evasive_answer": 0.25, "reasoning_inefficiency": 0.25}
    risk = min(1.0, sum(weights[f] for f in flags))

    base = base_confidence if base_confidence is not None else 0.5
    effective = round(max(0.0, base * (1.0 - risk)), 3)
    band = "high" if effective >= 0.7 else "medium" if effective >= 0.4 else "low"

    return {
        "epistemic_flags": flags,
        "epistemic_risk_score": round(risk, 3),
        "reasoning_efficiency_score": eff,
        "confidence_band": band,
        "effective_confidence": effective,
        "flag_details": details,
    }


__all__ = ["assess"]


if __name__ == "__main__":
    import json
    for a in ["The answer is definitely 42.",
              "It depends on the situation.",
              "Yes, it can; no, it cannot.",
              "Paris"]:
        print(a, "->", json.dumps(assess(a, reasoning_tokens=900, has_support=False)))
