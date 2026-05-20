"""DESi v3.47 — GAP geometry and cause analysis.

Compares the 2 terminal GAP_DETECTED cases against the
plateau (20), leakage (145) and rescued (228) cohorts
on a tail-aligned 45-d feature space and records per-
GAP cause classifications.
"""
from __future__ import annotations

from .cause import (
    GapCauseRecord, PLATEAU_PRIMARY_CAUSE,
    cause_distribution, classify_gap_cohort,
)
from .cluster import (
    CohortMember, gap_1nn_cluster_count, gap_members,
    leakage_members, plateau_members, rescued_members,
)
from .geometry import (
    TAIL_LENGTH, euclidean, final_state_vector,
    manifold_distance, tail_vector,
)
from .report import (
    V347Report, build_gap_geometry_artifact,
    build_report,
)


__all__ = [
    "CohortMember", "GapCauseRecord",
    "PLATEAU_PRIMARY_CAUSE", "TAIL_LENGTH",
    "V347Report", "build_gap_geometry_artifact",
    "build_report", "cause_distribution",
    "classify_gap_cohort", "euclidean",
    "final_state_vector", "gap_1nn_cluster_count",
    "gap_members", "leakage_members",
    "manifold_distance", "plateau_members",
    "rescued_members", "tail_vector",
]
