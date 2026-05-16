"""Closed enums for v5.3 corpus construction bias audit."""
from __future__ import annotations

from enum import Enum


class RewriteKind(str, Enum):
    """Closed taxonomy of rewrite types performed in
    v5.2."""

    NONE                     = "none"
    PROBE_AVOIDANCE          = "probe_avoidance"
    PROBE_ALIGNMENT          = "probe_alignment"
    SEMANTIC_PARAPHRASE      = "semantic_paraphrase"


class BiasRecommendation(str, Enum):
    """Aufgabe 10 closed gate."""

    UNBIASED            = "CORPUS_UNBIASED"
    PARTIALLY_BIASED    = "CORPUS_PARTIALLY_BIASED"
    FIT_TO_TAXONOMY     = "CORPUS_FIT_TO_TAXONOMY"
    NONE                = "NONE"


class NCKind(str, Enum):
    """Closed NC kinds for v5.3."""

    PROBE_ALIGNED_FAKE_INVALID = "probe_aligned_fake_invalid"
    PROBE_AVOIDING_FAKE_VALID  = "probe_avoiding_fake_valid"
    SEMANTIC_PARAPHRASE_TRAP   = "semantic_paraphrase_trap"
    LABEL_PRESERVING_SHIFT     = "label_preserving_shift"
    CROSS_DOMAIN_REWRITE       = "cross_domain_rewrite"


__all__ = [
    "BiasRecommendation", "NCKind", "RewriteKind",
]
