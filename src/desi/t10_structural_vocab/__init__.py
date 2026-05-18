"""DESi v3.115 - minimal structural alphabet."""
from __future__ import annotations

from .report import (
    RECOVERY_THRESHOLD,
    V3115Report,
    build_report,
    build_t10_structural_vocab_artifact,
)
from .search import (
    MAX_VOCAB_SIZE,
    SubsetOutcome,
    all_subset_outcomes,
    best_subset,
)
from .vocab import (
    complexity_cost,
    mean_auc,
    minimal_vocab_size,
    vocab_recovery,
)


__all__ = [
    "MAX_VOCAB_SIZE",
    "RECOVERY_THRESHOLD",
    "SubsetOutcome",
    "V3115Report",
    "all_subset_outcomes",
    "best_subset",
    "build_report",
    "build_t10_structural_vocab_artifact",
    "complexity_cost",
    "mean_auc",
    "minimal_vocab_size",
    "vocab_recovery",
]
