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
    """R1 (v1, FROZEN — used by the hard2 + hold-out results): p-value/significance
    used as a magnitude/importance claim, unqualified. Do not modify; see v2 below."""
    if _EFFECT_SIZE_QUALIFIER.search(text):
        return False
    return bool(_SIGNIFICANCE.search(text) and _MAGNITUDE.search(text))


# --- R1 v2: hardened on the sig_corpus DEV split only (v1 had 0.0 recall on novel
# phrasing). Broadens the significance markers, the magnitude lexicon and the
# effect-size guard, and adds a null-result guard. v1 is left untouched for
# reproducibility of the earlier committed results. ---

_SIG_MARKER_V2 = re.compile(
    r"\bp\s*(?:[<>=]|below|under|over|of|above)\s*0?\.\d+"
    r"|\bp[- ]?value"
    r"|\bstatistical(?:ly)?\s+significan"
    r"|\bstatistically\s+reliable"
    r"|\bsignifican(?:t|ce)\s+at\s+the\s+\d+\s*%"
    r"|\b(?:reached|achieved|hit|cleared|reaches)\s+significance"
    r"|\bsignificance\b"
    r"|\bsignificant(?:ly)?\b",
    re.I,
)
_NULL_RESULT = re.compile(
    r"\b(?:no|not|never|without|hardly)\s+(?:\w+\s+){0,3}significan"
    r"|n't\s+(?:\w+\s+){0,3}significan"
    r"|far from significance"
    r"|(?:did not|failed to|didn't)\s+reach\s+significance",
    re.I,
)
_MAGNITUDE_V2 = re.compile(
    r"\b(far more effective|more effective|highly effective|effective|outperform\w*|"
    r"superior|better|large|important|major|impact|dramatic\w*|substantial\w*|powerful|"
    r"strong(?:est|er|ly)?|prov(?:e|es|en|ing)|proof|works?|breakthrough|"
    r"game[- ]?changer|revolutionary|monumental|leap|markedly|enormous\w*|decisive\w*|"
    r"hugely|vastly|sharply|meaningful\w*|overwhelming\w*|by far|front[- ]?runner|"
    r"boosts?|beneficial|advance|must ship|game changer|clear (?:front[- ]?runner|winner))\b",
    re.I,
)
# effect-size qualifiers that correctly scope significance (BLOCK v2). Written to NOT
# match a SIG-positive's '5% level' or 'major practical impact'.
_EFFECT_SIZE_QUALIFIER_V2 = re.compile(
    r"\bd\s*=\s*0?\.\d+"
    r"|\beffect size\b"
    r"|\b(?:small|tiny|trivial|negligible|modest|minor)\b"
    r"|\bodds ratio\b"
    r"|\d+(?:\.\d+)?\s*%\s+of\s+variance"
    r"|\bof little\b|\blittle practical\b"
    r"|\bpractically (?:trivial|irrelevant|minor|negligible)\b"
    r"|\bclinically (?:minor|irrelevant|trivial|insignificant|negligible)\b"
    r"|\b0\.\d+\s*%"
    r"|\d+(?:\.\d+)?[- ]points?\b",
    re.I,
)


def detect_significance_not_importance_v2(text: str) -> bool:
    """Hardened R1: a (broadened) significance marker, not a null result, co-occurs with
    a (broadened) magnitude/importance claim, and no effect-size qualifier scopes it."""
    if _EFFECT_SIZE_QUALIFIER_V2.search(text):
        return False
    if _NULL_RESULT.search(text):
        return False
    return bool(_SIG_MARKER_V2.search(text) and _MAGNITUDE_V2.search(text))


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
