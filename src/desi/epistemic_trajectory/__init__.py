"""DESi v3.19 — Epistemic Trajectory Probe (read-only)."""
from __future__ import annotations

from .extractor import Trajectory, extract_all_trajectories
from .metrics import (
    TrajectoryMetrics, compute_centroid, compute_metrics,
)
from .negative_control import (
    ALL_NC_TRAJECTORIES, NCShape, NCTrajectory,
)
from .report import (
    DEAD_KNOB_DELTA,
    FRAME_TENSION_PRIMARY_THRESHOLD,
    MIN_NC_ACCURACY,
    MIN_SEPARABILITY,
    MIN_TRAJECTORY_COUNT,
    MIN_TRANSITION_COUNT,
    TrajectoryReport,
    build_trajectory_report,
)
from .state import DIMENSION_NAMES, StateVector, TrajectorySource

__all__ = [
    "ALL_NC_TRAJECTORIES",
    "DEAD_KNOB_DELTA",
    "DIMENSION_NAMES",
    "FRAME_TENSION_PRIMARY_THRESHOLD",
    "MIN_NC_ACCURACY",
    "MIN_SEPARABILITY",
    "MIN_TRAJECTORY_COUNT",
    "MIN_TRANSITION_COUNT",
    "NCShape",
    "NCTrajectory",
    "StateVector",
    "Trajectory",
    "TrajectoryMetrics",
    "TrajectoryReport",
    "TrajectorySource",
    "build_trajectory_report",
    "compute_centroid",
    "compute_metrics",
    "extract_all_trajectories",
]
