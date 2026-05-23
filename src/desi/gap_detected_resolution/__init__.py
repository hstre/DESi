"""DESi v3.48 — GAP_DETECTED resolution strategies.

Seven closed strategies tested against the 2 terminal
GAP cases. Reports best_strategy, per-strategy
overcontrol on the full corpus, and a verdict on
whether GAP_DETECTED is a robust terminal failure
class.
"""
from __future__ import annotations

from .resolution import (
    ResolutionOutcome, resolve_all_strategies_on_gaps,
    resolve_on_corpus,
)
from .report import (
    StrategyResult, V348Report,
    build_gap_resolution_artifact, build_report,
    build_terminal_gap_claims_artifact,
)
from .strategies import (
    StrategyKind, apply_strategy, strategy_a,
    strategy_b, strategy_c, strategy_d, strategy_e,
    strategy_f, strategy_g,
)


__all__ = [
    "ResolutionOutcome", "StrategyKind",
    "StrategyResult", "V348Report", "apply_strategy",
    "build_gap_resolution_artifact", "build_report",
    "build_terminal_gap_claims_artifact",
    "resolve_all_strategies_on_gaps",
    "resolve_on_corpus", "strategy_a", "strategy_b",
    "strategy_c", "strategy_d", "strategy_e",
    "strategy_f", "strategy_g",
]
