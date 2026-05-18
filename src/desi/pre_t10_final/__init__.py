"""DESi v3.120d - pre-T10 final rule."""
from __future__ import annotations

from .decision import (
    gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V3120dReport,
    build_pre_t10_final_rule_artifact,
    build_report,
)
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


__all__ = [
    "V3120dReport",
    "build_pre_t10_final_rule_artifact",
    "build_report",
    "calibration_window_exists",
    "final_adverse_flips",
    "final_far",
    "final_false_negative_rate",
    "final_historical_gate_flip_count",
    "final_rule_roi",
    "final_threshold",
    "final_threshold_drift",
    "final_tpr",
    "gate_failing_conditions",
    "gate_passes_all",
]
