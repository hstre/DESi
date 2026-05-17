"""DESi v3.43 — field-leakage census.

For every overcontrolled trajectory the v3.39
``frame_stability_condition`` policy produces, record
the geometric relationship to the plateau manifold so
v3.44 can probe whether a smaller policy radius
contains the leakage.
"""
from __future__ import annotations

from .census import (
    LeakageCase, collect_leakage_cases,
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from .distance import (
    euclidean, manifold_distance,
    per_state_dim_overlap, trajectory_vector,
)
from .report import (
    V343Report, build_leakage_inventory_artifact,
    build_manifold_distance_map_artifact,
    build_report,
)


__all__ = [
    "LeakageCase", "V343Report",
    "build_leakage_inventory_artifact",
    "build_manifold_distance_map_artifact",
    "build_report", "collect_leakage_cases",
    "collect_leakage_trajectories",
    "collect_plateau_anchors", "euclidean",
    "manifold_distance", "per_state_dim_overlap",
    "trajectory_vector",
]
