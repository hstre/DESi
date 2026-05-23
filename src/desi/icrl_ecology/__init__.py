"""DESi v19.3 - Long-Horizon Exploration Ecology
(read-only).

A >= 5000-step deterministic simulation of long-horizon
ICRL exploration. DESi keeps exploration plural, keeps
novelty visible, bounds policy drift, and resists
trajectory capture - forcing no path and injecting no
reward.
"""
from __future__ import annotations

from .ecology import (
    EVENT_TYPES, N_STEPS, SAMPLE_SIZE, EventType, StepState,
    enum_snapshot_hash, final_hash, mean_attempted_pressure,
    replay_hashes_match, run, sample,
)
from .exploration_pressure import (
    attempted_pressure, policy_drift, policy_drift_bounded,
    policy_drift_resistance,
)
from .novelty_decay import (
    min_novelty_visibility, novelty_stays_visible,
    novelty_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CAPTURED, VERDICT_HALT,
    VERDICT_STABLE, V193Report, build_ecology_artifact,
    build_report,
)
from .trajectory_memory import (
    capture_occurred, exploration_plurality, mean_capture,
    min_plurality, trajectory_capture_resistance,
)


__all__ = [
    "EVENT_TYPES",
    "N_STEPS",
    "REPORT_VERDICTS",
    "SAMPLE_SIZE",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "EventType",
    "StepState",
    "V193Report",
    "attempted_pressure",
    "build_ecology_artifact",
    "build_report",
    "capture_occurred",
    "enum_snapshot_hash",
    "exploration_plurality",
    "final_hash",
    "mean_attempted_pressure",
    "mean_capture",
    "min_novelty_visibility",
    "min_plurality",
    "novelty_stays_visible",
    "novelty_visibility",
    "policy_drift",
    "policy_drift_bounded",
    "policy_drift_resistance",
    "replay_hashes_match",
    "run",
    "sample",
    "trajectory_capture_resistance",
]
