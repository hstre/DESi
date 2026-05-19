"""DESi v8.3 - long-horizon persistent pressure
(read-only)."""
from __future__ import annotations

from .adaptation import (
    PRESSURE_STREAMS, STEP_COUNT, PressureStep,
    PressureStream, replay_trajectory,
    trajectory, trajectory_final_hash,
)
from .erosion import (
    erosion_rate, gate_violation_count,
    goal_mutation, governance_survival,
    opportunism_growth, replay_stability,
)
from .pressure_memory import (
    SHORT_WINDOW, early_window, late_window,
    mid_window,
)
from .report import (
    V83Report,
    build_long_horizon_pressure_artifact,
    build_report,
)


__all__ = [
    "PRESSURE_STREAMS",
    "PressureStep",
    "PressureStream",
    "SHORT_WINDOW",
    "STEP_COUNT",
    "V83Report",
    "build_long_horizon_pressure_artifact",
    "build_report",
    "early_window",
    "erosion_rate",
    "gate_violation_count",
    "goal_mutation",
    "governance_survival",
    "late_window",
    "mid_window",
    "opportunism_growth",
    "replay_stability",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
