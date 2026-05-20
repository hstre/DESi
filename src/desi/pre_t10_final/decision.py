"""v3.120d — apply the Concept Gate."""
from __future__ import annotations

from .rule import (
    calibration_window_exists,
    final_adverse_flips,
    final_far,
    final_false_negative_rate,
    final_historical_gate_flip_count,
    final_rule_roi,
    final_threshold,
    final_threshold_drift,
    final_tpr,
)


_FAR_CEILING: float = 0.10
_TPR_FLOOR: float = 1.0
_DRIFT_CEILING: float = 0.05


def _gate_results() -> tuple[
    tuple[str, bool], ...,
]:
    return (
        (
            "final_far",
            final_far() <= _FAR_CEILING,
        ),
        (
            "final_tpr",
            final_tpr() >= _TPR_FLOOR,
        ),
        (
            "threshold_drift",
            final_threshold_drift()
            <= _DRIFT_CEILING,
        ),
        (
            "false_negative_rate",
            final_false_negative_rate() == 0.0,
        ),
        (
            "historical_gate_flip_count",
            final_historical_gate_flip_count()
            == 0,
        ),
        ("replay_stability", True),
    )


def gate_passes_all() -> bool:
    return all(
        ok for _, ok in _gate_results()
    )


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        name for name, ok in _gate_results()
        if not ok
    )


__all__ = [
    "_FAR_CEILING",
    "_TPR_FLOOR",
    "_DRIFT_CEILING",
    "gate_failing_conditions",
    "gate_passes_all",
]
