"""Closed enums for v5.2 taxonomy generalization probe.

Five new adjacent domains; recommendation gate is a closed
three-value cascade plus NONE.
"""
from __future__ import annotations

from enum import Enum


class GeneralizationDomain(str, Enum):
    """Five new adjacent domains for the v5.2 evaluation
    corpus. Each is distinct from the v5.0 corpus
    domains."""

    D1_POSTMORTEM_ENGINEERING = "postmortem_engineering"
    D2_APPELLATE_LEGAL        = "appellate_legal"
    D3_CLINICAL_PROTOCOLS     = "clinical_protocols"
    D4_PEER_REVIEW_REBUTTAL   = "peer_review_rebuttal"
    D5_THEOREM_REVIEW         = "theorem_review"


class GeneralizationGroundTruth(str, Enum):
    VALID     = "VALID"
    INVALID   = "INVALID"
    AMBIGUOUS = "AMBIGUOUS"


class GeneralizationRecommendation(str, Enum):
    GENERALIZES = "TAXONOMY_GENERALIZES"
    PARTIAL     = "TAXONOMY_PARTIAL_GENERALIZATION"
    OVERFIT     = "TAXONOMY_OVERFIT"
    NONE        = "NONE"


class NoveltyKind(str, Enum):
    """Aufgabe 9 — closed novelty audit outcomes."""

    TRUE_NOVELTY        = "true_novelty"
    CLASSIFIER_UNCERT   = "classifier_uncertainty"
    TAXONOMY_MISS       = "taxonomy_miss"


class NCKind(str, Enum):
    """Aufgabe 10 — closed NC kinds for v5.2."""

    CROSS_DOMAIN_HYBRID    = "cross_domain_hybrid"
    LABEL_INVERSION        = "label_inversion"
    FAKE_OVERLAP_LOOP      = "fake_overlap_loop"
    FALSE_AMBIGUITY_TRAP   = "false_ambiguity_trap"
    SYNTHETIC_UNKNOWN      = "synthetic_unknown"


__all__ = [
    "GeneralizationDomain",
    "GeneralizationGroundTruth",
    "GeneralizationRecommendation",
    "NCKind", "NoveltyKind",
]
