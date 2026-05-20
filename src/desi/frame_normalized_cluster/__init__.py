"""DESi v3.90 — frame-normalized clustering.

Repeats the v3.86 blind clustering on the v3.89
residual projection of the novel anchor pool.
"""
from __future__ import annotations

from .cluster import (
    all_normalized_clusters,
    normalized_cluster_count,
    normalized_cluster_purity,
    normalized_cluster_recall,
    normalized_cluster_sizes,
    normalized_distance_gap,
    normalized_pairwise_distances,
)
from .normalize import (
    FrameCondition, frame_normalized_vectors,
)
from .report import (
    PURITY_THRESHOLD, RECALL_THRESHOLD,
    V390Report,
    build_frame_normalized_clusters_artifact,
    build_report,
)


__all__ = [
    "FrameCondition",
    "PURITY_THRESHOLD", "RECALL_THRESHOLD",
    "V390Report",
    "all_normalized_clusters",
    "build_frame_normalized_clusters_artifact",
    "build_report",
    "frame_normalized_vectors",
    "normalized_cluster_count",
    "normalized_cluster_purity",
    "normalized_cluster_recall",
    "normalized_cluster_sizes",
    "normalized_distance_gap",
    "normalized_pairwise_distances",
]
