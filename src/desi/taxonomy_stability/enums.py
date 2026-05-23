"""Closed enums for v5.1 taxonomy stability probe.

No runtime patching; these enums describe the perturbation
taxonomy and the recommendation gate only.
"""
from __future__ import annotations

from enum import Enum


class PerturbationFamily(str, Enum):
    """Closed family taxonomy for v5.1."""

    P1_REPRESENTATION_SWAP        = "representation_swap"
    P2_FEATURE_WEIGHT             = "feature_weight"
    P3_CORPUS_RESAMPLING          = "corpus_resampling"
    P4_ORDERING_NOISE             = "ordering_noise"
    P5_DOMAIN_MIX_SHIFT           = "domain_mix_shift"


class StabilityRecommendation(str, Enum):
    """Aufgabe 10 closed gate."""

    STABLE           = "TAXONOMY_STABLE"
    PARTIALLY_STABLE = "TAXONOMY_PARTIALLY_STABLE"
    UNSTABLE         = "TAXONOMY_UNSTABLE"
    NONE             = "NONE"


class NCKind(str, Enum):
    """Closed enumeration of NC types (Aufgabe 9)."""

    RANDOM_CLUSTERS     = "random_clusters"
    PERMUTED_LABELS     = "permuted_labels"
    BLENDED_CLUSTERS    = "blended_clusters"
    DUPLICATED_FEATURES = "duplicated_features"
    COLLAPSED_EMBEDDING = "collapsed_embedding"


__all__ = [
    "NCKind", "PerturbationFamily",
    "StabilityRecommendation",
]
