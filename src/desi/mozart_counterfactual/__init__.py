"""DESi v3.70 — Mozart counterfactual probe swap.

Replaces Mozart with historical and random-control
substitutes and measures the resulting coverage_loss
and input_specificity.
"""
from __future__ import annotations

from .counterfactual import (
    aggregate, mozart_baseline_score,
)
from .report import (
    V370Report,
    build_mozart_counterfactual_artifact,
    build_report,
)
from .swap import (
    RANDOM_CONTROL_COUNT, SwapResult,
    all_swap_results,
    deterministic_random_control_ids,
    input_specificity,
)


__all__ = [
    "RANDOM_CONTROL_COUNT", "SwapResult",
    "V370Report", "aggregate",
    "all_swap_results",
    "build_mozart_counterfactual_artifact",
    "build_report",
    "deterministic_random_control_ids",
    "input_specificity",
    "mozart_baseline_score",
]
