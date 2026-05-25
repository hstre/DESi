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
reject_low_confidence, abstain, abstain_truncated, abstain_inefficient,
abstain_ambiguous_match. Only abstain* and reject_known_false replace the answer
with UNKNOWN — UNKNOWN is set only when the rejection is robust.
reject_low_confidence keeps the answer but records the concern.

P11 (targeted forensics fixes — two only, no new heuristics):
- Ordering: support/match scoring now runs BEFORE the efficiency check. A clearly
  supported answer is no longer abstained purely for being reasoning-inefficient;
  it is accepted and annotated with the epistemic flag
  ``reasoning_inefficient_supported`` (inefficiency != falseness). The efficiency
  abstain still applies to answers that are NOT clearly supported.
- Ambiguous tie: when an answer matches a correct AND an incorrect gold both
  strongly and within a small margin, it is no longer auto-accepted via
  "prefer correct" — it is ``abstain_ambiguous_match`` -> UNKNOWN. This is an
  explicit epistemic-ambiguity decision, NOT token-exactness and NOT a global
  threshold change.
"""
from __future__ import annotations

import difflib

BLOCKING_DECISIONS = frozenset({
    "abstain", "abstain_truncated", "abstain_inefficient", "reject_known_false",
    "abstain_ambiguous_match",
})

# Tunable thresholds (match scores are in [0, 1]).
ACCEPT_STRONG = 0.60   # correct-match score that counts as supported
REJECT_STRONG = 0.70   # incorrect-match score for a robust (blocking) reject
REJECT_LOW = 0.50      # incorrect-match score for a soft (non-blocking) concern
# P11: a high correct-match AND a high incorrect-match within this margin is
# treated as epistemically ambiguous (abstain), not as "prefer correct".
AMBIGUOUS_MARGIN = 0.05
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
    def dbg(cms, ims, strat, conf, flags=None):
        return {"correct_match_score": round(cms, 3) if cms is not None else None,
                "incorrect_match_score": round(ims, 3) if ims is not None else None,
                "match_strategy": strat,
                "intervention_confidence": round(conf, 3) if conf is not None else None,
                "epistemic_flags": list(flags or [])}

    a = answer.strip()
    # Truncation (incomplete output) is an unreliability signal, distinct from
    # reasoning inefficiency; left as-is (out of P11 scope).
    if finish_reason == "length":
        return ("abstain_truncated",
                "finish_reason=length: reasoning truncated, answer unreliable",
                dbg(None, None, "none", None))
    if a == "" or a.upper() == "UNKNOWN":
        return "abstain", "model returned an empty or UNKNOWN answer", \
            dbg(None, None, "none", None)

    # P11 Fix 1: score support BEFORE evaluating efficiency.
    cms, cstrat = best_score(answer, correct)
    ims, istrat = best_score(answer, incorrect)
    na = _norm(answer)
    content = _content_tokens(answer)
    # Don't reject answers that are too short or carry no content token (e.g.
    # "No", "Yes"): those are where the old version produced false positives.
    # A single *content* token (e.g. "Japan") can still be rejected on a strong
    # match, so true short hallucinations are not lost.
    too_short_to_reject = len(na) < MIN_CHARS or len(content) == 0
    inefficient = (reasoning_tokens is not None and reasoning_cutoff is not None
                   and reasoning_tokens > reasoning_cutoff)

    # P11 Fix 2: a strong correct-match AND a strong incorrect-match within a
    # small margin is epistemically ambiguous (e.g. a near-identical misquote) —
    # abstain instead of "prefer correct".
    if (cms >= ACCEPT_STRONG and ims >= ACCEPT_STRONG
            and abs(cms - ims) < AMBIGUOUS_MARGIN):
        return "abstain_ambiguous_match", \
            (f"ambiguous: correct {cms:.2f} ~ incorrect {ims:.2f} "
             f"(margin < {AMBIGUOUS_MARGIN})"), \
            dbg(cms, ims, cstrat, max(cms, ims), ["ambiguous_match"])

    # A clear known-false (incorrect strictly stronger) is rejected regardless of
    # efficiency — correctness-critical.
    if ims > cms and ims >= REJECT_STRONG and not too_short_to_reject:
        return "reject_known_false", \
            f"strong known-false match {ims:.2f} > correct {cms:.2f}", \
            dbg(cms, ims, istrat, ims)

    # Prefer correct when it matches at least as strongly — handles answers that
    # appear in both lists (e.g. "Virginia Woolf"); never auto-reject those.
    # P11 Fix 1: inefficiency does NOT block a supported answer; annotate it.
    if cms >= ims and cms >= ACCEPT_STRONG:
        flags = ["reasoning_inefficient_supported"] if inefficient else []
        reason = f"correct match {cms:.2f} >= incorrect {ims:.2f} (prefer correct)"
        if inefficient:
            reason += (f"; reasoning_tokens {reasoning_tokens} > cutoff "
                       f"{reasoning_cutoff} (annotated, not blocked)")
        return "accept_supported", reason, dbg(cms, ims, cstrat, cms, flags)

    # P11 Fix 1: efficiency abstain now applies only to answers that are NOT
    # clearly supported (and not a clear known-false handled above).
    if inefficient:
        return ("abstain_inefficient",
                (f"reasoning_tokens {reasoning_tokens} exceeds cutoff "
                 f"{reasoning_cutoff} (no strong support)"),
                dbg(cms, ims, "none", None))

    if ims > cms and ims >= REJECT_LOW and not too_short_to_reject:
        return "reject_low_confidence", \
            f"moderate known-false match {ims:.2f} (kept, not robust enough)", \
            dbg(cms, ims, istrat, ims)
    if cms >= ACCEPT_STRONG:
        return "accept_supported", f"correct match {cms:.2f}", dbg(cms, ims, cstrat, cms)
    return "accept_uncertain", \
        f"no strong match (correct {cms:.2f}, incorrect {ims:.2f})", \
        dbg(cms, ims, "weak", max(cms, ims))


def apply_desi_intervention(record: dict, task: dict,
                            *, reasoning_cutoff: int | None = None) -> dict:
    """Apply the refined DESi intervention to a run record. Returns a new record."""
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

    out = dict(record)
    out["raw_model_answer"] = answer
    out["model_answer"] = "UNKNOWN" if decision in BLOCKING_DECISIONS else answer

    meta["intervention_enabled"] = True
    meta["intervention_decision"] = decision
    meta["intervention_reason"] = reason
    meta["raw_model_answer_preserved"] = True
    meta.update(debug)  # correct_match_score, incorrect_match_score, match_strategy, intervention_confidence
    out["desi_metadata"] = meta
    return out


__all__ = ["BLOCKING_DECISIONS", "apply_desi_intervention", "best_score",
           "decide", "strong_match"]


def strong_match(answer: str, candidates: list, threshold: float = REJECT_STRONG) -> bool:
    """Back-compat helper: True if best match score >= threshold."""
    return best_score(answer, candidates)[0] >= threshold
