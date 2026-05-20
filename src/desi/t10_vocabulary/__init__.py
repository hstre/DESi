"""DESi v3.108 - T10 expansion vocabulary
decision.
"""
from __future__ import annotations

from .decision import (
    StrategyOutcome,
    all_strategy_outcomes,
    architecture_roi,
    best_strategy,
    complexity_score,
    recovery_score,
    stability_score,
)
from .report import (
    V3108Report,
    build_report,
    build_t10_expansion_vocabulary_artifact,
)
from .vocabulary import (
    ExpansionStrategy,
    case_specific_dims,
    single_universal_dims,
    small_vocab_dims,
    strategy_dims,
)


__all__ = [
    "ExpansionStrategy",
    "StrategyOutcome",
    "V3108Report",
    "all_strategy_outcomes",
    "architecture_roi",
    "best_strategy",
    "build_report",
    "build_t10_expansion_vocabulary_artifact",
    "case_specific_dims",
    "complexity_score",
    "recovery_score",
    "single_universal_dims",
    "small_vocab_dims",
    "stability_score",
    "strategy_dims",
]
