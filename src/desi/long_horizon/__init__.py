"""DESi v5.3 - long-horizon stability."""
from __future__ import annotations

from .drift import (
    drift_acceleration, early_curiosity,
    gate_violation_count, goal_shift,
    governance_integrity, late_curiosity,
    self_amplification,
)
from .entropy import (
    contradiction_growth, early_entropy,
    entropy_growth, frame_explosion,
    frame_universe_seen, late_entropy,
)
from .report import (
    V53Report,
    build_long_horizon_stability_artifact,
    build_report, replay_stability,
)
from .stability import (
    LongHorizonStep, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)


__all__ = [
    "LongHorizonStep",
    "STEP_COUNT",
    "V53Report",
    "build_long_horizon_stability_artifact",
    "build_report",
    "contradiction_growth",
    "drift_acceleration",
    "early_curiosity",
    "early_entropy",
    "entropy_growth",
    "frame_explosion",
    "frame_universe_seen",
    "gate_violation_count",
    "goal_shift",
    "governance_integrity",
    "late_curiosity",
    "late_entropy",
    "replay_stability",
    "replay_trajectory",
    "self_amplification",
    "trajectory",
    "trajectory_final_hash",
]
