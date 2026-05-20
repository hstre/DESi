"""DESi v3.37 — self-explanation audit.

For every trajectory the v3.35 Strategy B intervention
moved, ask DESi the directive's self-question
"Why did I rescue this trajectory?" and emit a
machine-readable answer. The 14 unexpected rescues are
the gate cohort; the 20 plateau resolutions are
included for symmetry.
"""
from __future__ import annotations

from .attribution import (
    confidence_hold_was_noop, decisive_dimension,
    first_changed_dimension,
)
from .counterfactual import (
    DimensionDelta, per_dimension_deltas,
    strategy_b_counterfactual,
)
from .explainer import (
    PLATEAU_PRIMARY_CAUSE, SelfExplanation,
    collect_movers, explain_all_movers, explain_one,
    explain_unexpected_rescues,
)
from .report import (
    EXPECTED_RESCUE_COUNT, MAX_UNEXPLAINED_CASES,
    V337Report, build_overgeneralized_claims_artifact,
    build_report, build_self_explanation_artifact,
)


__all__ = [
    "DimensionDelta", "EXPECTED_RESCUE_COUNT",
    "MAX_UNEXPLAINED_CASES", "PLATEAU_PRIMARY_CAUSE",
    "SelfExplanation", "V337Report",
    "build_overgeneralized_claims_artifact",
    "build_report", "build_self_explanation_artifact",
    "collect_movers", "confidence_hold_was_noop",
    "decisive_dimension", "explain_all_movers",
    "explain_one", "explain_unexpected_rescues",
    "first_changed_dimension", "per_dimension_deltas",
    "strategy_b_counterfactual",
]
