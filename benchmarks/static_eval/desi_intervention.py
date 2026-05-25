#!/usr/bin/env python3
"""DESi intervention layer (refined) for the static-eval pipeline.

After the LLM call, DESi decides whether to accept / abstain / reject and may
replace a blocked answer with an explicit ``UNKNOWN`` (preserving the original as
``raw_model_answer``). This refinement targets the false positives of the first
version (short/ambiguous answers like "No" or "Virginia Woolf" were rejected):

- Matching is normalized (lowercase, strip punctuation, collapse whitespace) and
  combines exact match, token overlap (stopword-filtered), and a lightweight
  stdlib fuzzy ratio (``difflib``) — no more raw substring overlap.
- Very short answers (< 3 chars or < 2 tokens) are rejected ONLY on an *exact*
  known-false match (so "Japan"==a known-false answer still blocks, but "No"
  does not).
- If an answer matches both correct and incorrect lists, the stronger side wins
  (prefer correct), so it is not auto-rejected.

Decisions: accept_supported, accept_uncertain, reject_known_false,
reject_low_confidence, abstain, abstain_truncated, abstain_inefficient. Only
abstain* and reject_known_false replace the answer with UNKNOWN — UNKNOWN is set
only when the rejection is robust. reject_low_confidence keeps the answer but
records the concern.
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # for general_epistemic_checks

# Only these replace the answer with UNKNOWN. The general epistemic decisions
# (reject_contradictory, reject_unsupported_certainty, downgrade_low_evidence,
# accept_low_confidence) are NON-blocking: they flag/annotate and reduce
# confidence but keep the answer. UNKNOWN is set only on robust known-false
# evidence or truncation/inefficiency.
BLOCKING_DECISIONS = frozenset({
    "abstain", "abstain_truncated", "abstain_inefficient", "reject_known_false",
})

# Tunable thresholds (match scores are in [0, 1]).
ACCEPT_STRONG = 0.60   # correct-match score that counts as supported
REJECT_STRONG = 0.70   # incorrect-match score for a robust (blocking) reject
REJECT_LOW = 0.50      # incorrect-match score for a soft (non-blocking) concern
MIN_CHARS = 3
MIN_TOKENS = 2

_STOP = frozenset({
    "the", "a", "an", "of", "to", "is", "are", "in", "on", "and", "or", "that",
    "it", "this", "be", "as", "by", "for", "with", "was", "were", "no", "not",
    "yes", "do", "does", "did", "can", "will", "would", "you", "your",
})


def _norm(s: object) -> str:
    out = "".join(c if c.isalnum() or c.isspace() else " " for c in str(s).lower())
    return " ".join(out.split())


def _content_tokens(s: str) -> set:
    return {t for t in _norm(s).split() if t not in _STOP}


def _pair_score(answer: str, candidate: str) -> tuple[float, str]:
    na, nc = _norm(answer), _norm(candidate)
    if not na or not nc:
        return 0.0, "none"
    if na == nc:
        return 1.0, "exact"
    at, ct = _content_tokens(answer), _content_tokens(candidate)
    containment = (len(at & ct) / len(at)) if at else 0.0
    fuzzy = difflib.SequenceMatcher(None, na, nc).ratio()
    if containment >= fuzzy:
        return containment, "token_overlap"
    return fuzzy, "fuzzy"


def best_score(answer: str, candidates: list) -> tuple[float, str]:
    best, strat = 0.0, "none"
    for c in candidates or []:
        s, st = _pair_score(answer, c)
        if s > best:
            best, strat = s, st
    return best, strat


def _exact_match(answer: str, candidates: list) -> bool:
    na = _norm(answer)
    return bool(na) and any(na == _norm(c) for c in (candidates or []))


def decide(answer: str, finish_reason: str | None, reasoning_tokens: int | None,
           reasoning_cutoff: int | None, correct: list, incorrect: list
           ) -> tuple[str, str, dict]:
    def dbg(cms, ims, strat, conf):
        return {"correct_match_score": round(cms, 3) if cms is not None else None,
                "incorrect_match_score": round(ims, 3) if ims is not None else None,
                "match_strategy": strat,
                "intervention_confidence": round(conf, 3) if conf is not None else None}

    a = answer.strip()
    if finish_reason == "length":
        return ("abstain_truncated",
                "finish_reason=length: reasoning truncated, answer unreliable",
                dbg(None, None, "none", None))
    if (reasoning_tokens is not None and reasoning_cutoff is not None
            and reasoning_tokens > reasoning_cutoff):
        return ("abstain_inefficient",
                f"reasoning_tokens {reasoning_tokens} exceeds cutoff {reasoning_cutoff}",
                dbg(None, None, "none", None))
    if a == "" or a.upper() == "UNKNOWN":
        return "abstain", "model returned an empty or UNKNOWN answer", \
            dbg(None, None, "none", None)

    cms, cstrat = best_score(answer, correct)
    ims, istrat = best_score(answer, incorrect)
    na = _norm(answer)
    content = _content_tokens(answer)
    # Don't reject answers that are too short or carry no content token (e.g.
    # "No", "Yes"): those are where the old version produced false positives.
    # A single *content* token (e.g. "Japan") can still be rejected on a strong
    # match, so true short hallucinations are not lost.
    too_short_to_reject = len(na) < MIN_CHARS or len(content) == 0

    # Prefer correct when it matches at least as strongly — handles answers that
    # appear in both lists (e.g. "Virginia Woolf"); never auto-reject those.
    if cms >= ims and cms >= ACCEPT_STRONG:
        return "accept_supported", \
            f"correct match {cms:.2f} >= incorrect {ims:.2f} (prefer correct)", \
            dbg(cms, ims, cstrat, cms)
    if ims > cms and ims >= REJECT_STRONG and not too_short_to_reject:
        return "reject_known_false", \
            f"strong known-false match {ims:.2f} > correct {cms:.2f}", \
            dbg(cms, ims, istrat, ims)
    if ims > cms and ims >= REJECT_LOW and not too_short_to_reject:
        return "reject_low_confidence", \
            f"moderate known-false match {ims:.2f} (kept, not robust enough)", \
            dbg(cms, ims, istrat, ims)
    if cms >= ACCEPT_STRONG:
        return "accept_supported", f"correct match {cms:.2f}", dbg(cms, ims, cstrat, cms)
    return "accept_uncertain", \
        f"no strong match (correct {cms:.2f}, incorrect {ims:.2f})", \
        dbg(cms, ims, "weak", max(cms, ims))


def apply_desi_intervention(record: dict, task: dict, *,
                            reasoning_cutoff: int | None = None,
                            general_checks: bool = True) -> dict:
    """Apply the refined DESi intervention to a run record. Returns a new record.

    The dataset-guided decision (decide) determines blocking. When
    ``general_checks`` is on, dataset-independent epistemic risk signals are
    added: they only flag, annotate the decision, and reduce confidence — they
    never set UNKNOWN on their own.
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

    decision, reason, debug = decide(answer, finish_reason, reasoning_tokens,
                                     cutoff, correct, incorrect)
    blocked = decision in BLOCKING_DECISIONS
    final_answer = "UNKNOWN" if blocked else answer  # epistemic checks never block

    epi = {}
    if general_checks:
        from general_epistemic_checks import assess
        epi = assess(answer, reasoning_tokens=reasoning_tokens,
                     finish_reason=finish_reason,
                     has_support=(decision == "accept_supported"),
                     base_confidence=debug.get("intervention_confidence"))
        # Annotate low-evidence accepts with a general epistemic decision (still
        # non-blocking). Strong dataset-guided decisions are left untouched.
        if not blocked and decision in ("accept_uncertain", "reject_low_confidence"):
            flags = epi["epistemic_flags"]
            if "contradiction" in flags:
                decision = "reject_contradictory"
            elif "unsupported_certainty" in flags:
                decision = "reject_unsupported_certainty"
            elif "evasive_answer" in flags or epi["epistemic_risk_score"] >= 0.4:
                decision = "downgrade_low_evidence"
            elif decision == "accept_uncertain":
                decision = "accept_low_confidence"

    out = dict(record)
    out["raw_model_answer"] = answer
    out["model_answer"] = final_answer

    meta["intervention_enabled"] = True
    meta["intervention_decision"] = decision
    meta["intervention_reason"] = reason
    meta["raw_model_answer_preserved"] = True
    meta.update(debug)
    if epi:
        meta["epistemic_flags"] = epi["epistemic_flags"]
        meta["epistemic_risk_score"] = epi["epistemic_risk_score"]
        meta["reasoning_efficiency_score"] = epi["reasoning_efficiency_score"]
        meta["confidence_band"] = epi["confidence_band"]
        meta["intervention_confidence"] = epi["effective_confidence"]  # epistemic-adjusted
    out["desi_metadata"] = meta
    return out


__all__ = ["BLOCKING_DECISIONS", "apply_desi_intervention", "best_score",
           "decide", "strong_match"]


def strong_match(answer: str, candidates: list, threshold: float = REJECT_STRONG) -> bool:
    """Back-compat helper: True if best match score >= threshold."""
    return best_score(answer, candidates)[0] >= threshold
