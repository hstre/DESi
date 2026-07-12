"""Deterministic epistemic rules — 'rules for logic', no LLM.

The hard2 benchmark exposed two failure modes that even frontier LLMs share
(REDTEAM_HARD2_RESULT.md): they systematically miss ``significance_not_importance``
(per-flag recall 0.43) and they over-flag ``overclaim`` on well-supported claims
(the most false positives of any flag). Both are *codifiable* — they turn on the
presence/absence of specific, checkable textual markers rather than on judgement.

This module codifies exactly those two patterns as deterministic functions of the
excerpt text (plus, for suppression, the flags the language model already raised).
It is a post-layer over an LLM reviewer: the LLM handles language, the rule handles
the two logically-decidable checks.

IMPORTANT — the patterns are derived from the flag *definitions* in ``prompt.py``,
NOT tuned against the gold labels of the 18 hard2 items. Two general rules:

  R1 (add significance_not_importance): a p-value / significance marker CO-OCCURS
     with a magnitude-or-importance claim, and NO effect-size qualifier separates
     them. ("p < 0.001, so it is far more effective" → yes; "significant, but the
     effect was small" → no.)

  R2 (suppress overclaim): the LLM raised ``overclaim``, but the text carries strong
     support/hedge markers (specific reference, CI, pre-registration, 'consistent
     with', a stated scope limit) AND no over-generalisation verb. A carefully
     hedged, sourced claim is not an overclaim.

Whatever these blind rules do to the score — including any new errors they introduce
on other items — is reported honestly by the harness; nothing here peeks at gold.
"""
from __future__ import annotations

import re

from .items import Flag2

# --- R1: significance-vs-importance ---------------------------------------------

# a statistical-significance marker: an explicit p-value, or the words themselves.
_SIGNIFICANCE = re.compile(
    r"\bp\s*[<>=]\s*0?\.\d+|\bp[- ]?value|\bstatistical(?:ly)?\s+significan|\bsignificance\b",
    re.I,
)
# a magnitude / practical-importance claim riding on that significance.
_MAGNITUDE = re.compile(
    r"\b(far more effective|more effective|highly effective|large effect|big effect|"
    r"strong(?:ly)? effect|dramatic|clearly|proof|proves?|works?\b|should replace|"
    r"most effective|substantial(?:ly)?)\b",
    re.I,
)
# an effect-size qualifier that correctly separates significance from magnitude.
# Its presence BLOCKS R1 (the text already distinguishes the two).
_EFFECT_SIZE_QUALIFIER = re.compile(
    r"\b(effect (?:was|is) small|small effect|modest effect|effect size|"
    r"half a point|clinical(?:ly)? (?:importance|significance) (?:is )?limited|"
    r"limited (?:clinical )?importance|not (?:necessarily )?large)\b",
    re.I,
)


def detect_significance_not_importance(text: str) -> bool:
    """R1: p-value/significance used as a magnitude/importance claim, unqualified."""
    if _EFFECT_SIZE_QUALIFIER.search(text):
        return False
    return bool(_SIGNIFICANCE.search(text) and _MAGNITUDE.search(text))


# --- R2: overclaim suppression ---------------------------------------------------

# markers that a claim is specifically sourced / hedged / scope-limited.
_SUPPORT = re.compile(
    r"\b(consistent with|do not generalize|does not generalize|pre-?registered|"
    r"pre-?registration|confidence interval|\b95% ci|stopping rule|appendix|\beq\.?\s*\d|"
    r"\bfig(?:ure)?\s*\d|\bpdb\b|analysis code|code deposited|co-crystal|"
    r"under the stated assumptions|modest)\b",
    re.I,
)
# over-generalisation / proof language: if present, the claim really does overreach,
# so suppression is blocked.
_OVERGENERALISATION = re.compile(
    r"\b(all patients|every patient|everyone|for all\b|national|mandat(?:e|ing)|"
    r"should replace|proof|proves?|beyond question|objectively|raise national|"
    r"cannot be|will (?:reduce|raise|lower|change))\b",
    re.I,
)


def suppress_overclaim(text: str) -> bool:
    """R2: True if a raised ``overclaim`` should be removed (well-supported, in-scope)."""
    if _OVERGENERALISATION.search(text):
        return False
    return bool(_SUPPORT.search(text))


def apply_rules(text: str, llm_flags: set[Flag2]) -> set[Flag2]:
    """Post-process one excerpt's LLM flag set with the two deterministic rules."""
    out = set(llm_flags)
    if detect_significance_not_importance(text):
        out.add(Flag2.SIGNIFICANCE_NOT_IMPORTANCE)
    if Flag2.OVERCLAIM in out and suppress_overclaim(text):
        out.discard(Flag2.OVERCLAIM)
    return out


__all__ = ["detect_significance_not_importance", "suppress_overclaim", "apply_rules"]
