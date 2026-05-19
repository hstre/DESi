"""DESi v6.3 - long-horizon world contact
(read-only)."""
from __future__ import annotations

from .memory import (
    LONG_WINDOW, SHORT_WINDOW, early_window,
    late_window, long_window, short_window,
)
from .report import (
    V63Report, blindness_delta,
    build_long_horizon_world_contact_artifact,
    build_report, drift_rate,
    gate_violation_count, governance_survival,
    hallucination_growth, replay_stability,
)
from .uncertainty import (
    early_distribution, high_certainty_rate,
    late_distribution, low_certainty_rate,
    total_variation_drift,
)
from .world_drift import (
    STEP_COUNT, STREAM_KINDS, StreamKind,
    WorldStep, replay_trajectory, trajectory,
    trajectory_final_hash,
)


__all__ = [
    "LONG_WINDOW",
    "SHORT_WINDOW",
    "STEP_COUNT",
    "STREAM_KINDS",
    "StreamKind",
    "V63Report",
    "WorldStep",
    "blindness_delta",
    "build_long_horizon_world_contact_artifact",
    "build_report",
    "drift_rate",
    "early_distribution",
    "early_window",
    "gate_violation_count",
    "governance_survival",
    "hallucination_growth",
    "high_certainty_rate",
    "late_distribution",
    "late_window",
    "long_window",
    "low_certainty_rate",
    "replay_stability",
    "replay_trajectory",
    "short_window",
    "total_variation_drift",
    "trajectory",
    "trajectory_final_hash",
]
