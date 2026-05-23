"""DESi v3.97 — text-only semantic loss audit
between G_v316susp and E_v317h.
"""
from __future__ import annotations

from .divergence import (
    ConceptAssignment, ConceptKind,
    all_concept_assignments,
    classify_text,
    concept_distribution_by_family,
    concept_divergence,
    dominant_concept_per_family,
)
from .report import (
    SEMANTIC_DISTANCE_THRESHOLD,
    V397Report,
    build_report,
    build_semantic_loss_audit_artifact,
)
from .semantic_loss import (
    ENTANGLED_FAMILY_IDS,
    FamilyTokenStats,
    family_token_stats,
    family_uniqueness,
    jaccard_bigrams, jaccard_unigrams,
    semantic_distance, semantic_overlap,
)


__all__ = [
    "ConceptAssignment", "ConceptKind",
    "ENTANGLED_FAMILY_IDS",
    "FamilyTokenStats",
    "SEMANTIC_DISTANCE_THRESHOLD",
    "V397Report",
    "all_concept_assignments",
    "build_report",
    "build_semantic_loss_audit_artifact",
    "classify_text",
    "concept_distribution_by_family",
    "concept_divergence",
    "dominant_concept_per_family",
    "family_token_stats",
    "family_uniqueness",
    "jaccard_bigrams", "jaccard_unigrams",
    "semantic_distance", "semantic_overlap",
]
