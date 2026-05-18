"""DESi v3.124 — pre-T10 v2 deployment decision."""
from __future__ import annotations

from .decision import (
    STRATEGIES, Strategy, StrategyMetrics,
    all_strategy_metrics, best_strategy,
    disqualified_strategies,
    metrics_multi_signal, metrics_no_precheck,
    metrics_single_threshold,
)
from .report import (
    V3124Report,
    build_pre_t10_v2_go_no_go_artifact,
    build_report,
)


__all__ = [
    "STRATEGIES",
    "Strategy",
    "StrategyMetrics",
    "V3124Report",
    "all_strategy_metrics",
    "best_strategy",
    "build_pre_t10_v2_go_no_go_artifact",
    "build_report",
    "disqualified_strategies",
    "metrics_multi_signal",
    "metrics_no_precheck",
    "metrics_single_threshold",
]
