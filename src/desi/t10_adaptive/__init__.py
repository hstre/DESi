"""DESi v3.107 - T10 adaptive candidate search."""
from __future__ import annotations

from .adaptive import (
    ADAPTIVE_CANDIDATES, ALL_CANDIDATES,
    AdaptiveCandidate,
    adaptive_value,
    candidate_values_for_ids,
)
from .report import (
    V3107Report,
    build_report,
    build_t10_adaptive_candidates_artifact,
    candidate_vocab_size,
    mean_candidate_auc,
    new_candidate_count,
    rescue_rate,
    reused_candidates,
    used_candidates,
)
from .search import (
    AdaptiveOutcome,
    all_adaptive_outcomes,
)


__all__ = [
    "ADAPTIVE_CANDIDATES",
    "ALL_CANDIDATES",
    "AdaptiveCandidate",
    "AdaptiveOutcome",
    "V3107Report",
    "adaptive_value",
    "all_adaptive_outcomes",
    "build_report",
    "build_t10_adaptive_candidates_artifact",
    "candidate_values_for_ids",
    "candidate_vocab_size",
    "mean_candidate_auc",
    "new_candidate_count",
    "rescue_rate",
    "reused_candidates",
    "used_candidates",
]
