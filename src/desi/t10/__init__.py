"""DESi v3.101 - T10 representational expansion
trigger: candidate dimension search.
"""
from __future__ import annotations

from .candidate import (
    CANDIDATE_DIMS, CandidateDim,
    candidate_values,
)
from .report import (
    AUC_THRESHOLD,
    V3101Report,
    build_report,
    build_t10_dimension_search_artifact,
)
from .search import (
    CandidateOutcome,
    all_candidate_outcomes,
    augmented_vectors,
    best_outcome,
    candidates_above_auc_threshold,
    has_dominant_candidate,
)


__all__ = [
    "AUC_THRESHOLD",
    "CANDIDATE_DIMS",
    "CandidateDim",
    "CandidateOutcome",
    "V3101Report",
    "all_candidate_outcomes",
    "augmented_vectors",
    "best_outcome",
    "build_report",
    "build_t10_dimension_search_artifact",
    "candidate_values",
    "candidates_above_auc_threshold",
    "has_dominant_candidate",
]
