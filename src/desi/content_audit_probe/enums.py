"""Closed taxonomies for v4.8 — content-failure class +
counterfactual content probes + recommendation outcome."""
from __future__ import annotations

from enum import Enum


class ContentFailure(str, Enum):
    """Closed content-failure taxonomy (Aufgabe 5). Every
    residual false-support case maps to exactly one value.

    Priority order during classification (most specific first):

    1. DIRECT_CONTRADICTION       (premise asserts X, conclusion ¬X)
    2. PROPERTY_REVERSAL          (premise +polarity, conclusion -polarity)
    3. CAUSE_EFFECT_INVERSION     (cause/effect direction flipped)
    4. NECESSARY_SUFFICIENT_SWAP  (necessary↔sufficient conflated)
    5. LOCAL_GLOBAL_SUBSTITUTION  (single observation → universal)
    6. ENTITY_ALIAS_COLLISION     (two entities silently identified)
    7. EXCEPTION_ERASURE          (qualifier dropped between premise/concl)
    8. WARRANT_FREE_ANALOGY       (analogy without warrant)
    9. UNKNOWN                    (catch-all)
    """

    DIRECT_CONTRADICTION       = "DIRECT_CONTRADICTION"
    PROPERTY_REVERSAL          = "PROPERTY_REVERSAL"
    CAUSE_EFFECT_INVERSION     = "CAUSE_EFFECT_INVERSION"
    NECESSARY_SUFFICIENT_SWAP  = "NECESSARY_SUFFICIENT_SWAP"
    LOCAL_GLOBAL_SUBSTITUTION  = "LOCAL_GLOBAL_SUBSTITUTION"
    ENTITY_ALIAS_COLLISION     = "ENTITY_ALIAS_COLLISION"
    EXCEPTION_ERASURE          = "EXCEPTION_ERASURE"
    WARRANT_FREE_ANALOGY       = "WARRANT_FREE_ANALOGY"
    UNKNOWN                    = "UNKNOWN"


class ContentProbe(str, Enum):
    """Five closed counterfactual content probes (Aufgabe 6)."""

    C1_CONTRADICTION_PAIR_CHECK     = "C1_contradiction_pair_check"
    C2_POLARITY_FLIP_CHECK          = "C2_polarity_flip_check"
    C3_CAUSE_DIRECTION_CHECK        = "C3_cause_direction_check"
    C4_NECESSITY_SUFFICIENCY_CHECK  = "C4_necessity_sufficiency_check"
    C5_ENTITY_CONSISTENCY_CHECK     = "C5_entity_consistency_check"


class RecommendationOutcome(str, Enum):
    LOCALIZED = "CONTENT_FAILURE_LOCALIZED"
    DIFFUSE   = "CONTENT_FAILURE_DIFFUSE"
    UNKNOWN   = "CONTENT_FAILURE_UNKNOWN"
    NONE      = "NONE"


__all__ = [
    "ContentFailure", "ContentProbe", "RecommendationOutcome",
]
