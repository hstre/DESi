"""v3.120d — final pre-T10 rule decision.

The rule is the v3.120 single-threshold check.
Activation is gated on the joint outcome of
v3.120a (sweep feasibility), v3.120b (bootstrap
stability), v3.120c (stress replay), and
v3.120's own historical-flip count.
"""
from __future__ import annotations

from ..pre_t10_bootstrap.stability import (
    threshold_drift,
)
from ..pre_t10_calibration.sweep import (
    feasible_cells,
)
from ..pre_t10_rule.decision import (
    BLINDNESS_CHECK_THRESHOLD,
    false_activation_rate,
    historical_gate_flip_count,
    rule_roi,
    true_case_recall,
)
from ..pre_t10_stress.historical import (
    adverse_flip_count,
    false_negative_rate_max,
)


def final_threshold() -> float:
    return BLINDNESS_CHECK_THRESHOLD()


def final_far() -> float:
    return false_activation_rate()


def final_tpr() -> float:
    return true_case_recall()


def final_threshold_drift() -> float:
    return threshold_drift()


def final_adverse_flips() -> int:
    return adverse_flip_count()


def final_false_negative_rate() -> float:
    return false_negative_rate_max()


def final_rule_roi() -> float:
    return rule_roi()


def final_historical_gate_flip_count() -> int:
    return historical_gate_flip_count()


def calibration_window_exists() -> bool:
    return len(feasible_cells()) > 0


__all__ = [
    "calibration_window_exists",
    "final_adverse_flips",
    "final_far",
    "final_false_negative_rate",
    "final_historical_gate_flip_count",
    "final_rule_roi",
    "final_threshold",
    "final_threshold_drift",
    "final_tpr",
]
