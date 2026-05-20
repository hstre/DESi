"""DESi v3.86 — blind doppelganger clustering on the
v3.85 novel claim families. Same algorithm as v3.81,
applied to anchors never seen by any prior sprint.
"""
from __future__ import annotations

from .cluster import (
    all_novel_blind_clusters,
    cluster_purity, cluster_recall,
    cluster_sizes,
    predicted_cluster_count,
)
from .distance import (
    novel_anchor_vectors,
    novel_distance_gap,
    novel_pairwise_distances,
)
from .report import (
    PURITY_THRESHOLD, RECALL_THRESHOLD,
    V386Report,
    build_novel_family_clusters_artifact,
    build_report,
)


__all__ = [
    "PURITY_THRESHOLD", "RECALL_THRESHOLD",
    "V386Report",
    "all_novel_blind_clusters",
    "build_novel_family_clusters_artifact",
    "build_report",
    "cluster_purity", "cluster_recall",
    "cluster_sizes",
    "novel_anchor_vectors",
    "novel_distance_gap",
    "novel_pairwise_distances",
    "predicted_cluster_count",
]
