"""DESi v3.76 — blind multi-claim recovery.

Hides a 3-anchor subset of the v3.73 test claim set
and asks DESi to infer how many claims are missing,
where they were, and what role each played - all
from the orphan-leakage pattern alone.
"""
from __future__ import annotations

from .blind import (
    CLUSTER_DISTANCE_THRESHOLD, HIDDEN_ROLES,
    HIDDEN_SUBSET, OrphanCluster,
    cluster_orphans, orphan_indices, visible_set,
)
from .recover import (
    CLUSTER_SIZE_BRIDGE_CEILING,
    ClusterAssignment, assign_clusters,
    false_reconstruction_rate,
    missing_count_error,
    predicted_distinct_regions,
    region_recall, role_recall,
)
from .report import (
    NEPTUN_REGION_RECALL_FLOOR, V376Report,
    build_blind_recovery_artifact, build_report,
)


__all__ = [
    "CLUSTER_DISTANCE_THRESHOLD",
    "CLUSTER_SIZE_BRIDGE_CEILING",
    "ClusterAssignment", "HIDDEN_ROLES",
    "HIDDEN_SUBSET",
    "NEPTUN_REGION_RECALL_FLOOR",
    "OrphanCluster", "V376Report",
    "assign_clusters",
    "build_blind_recovery_artifact",
    "build_report", "cluster_orphans",
    "false_reconstruction_rate",
    "missing_count_error", "orphan_indices",
    "predicted_distinct_regions",
    "region_recall", "role_recall",
    "visible_set",
]
