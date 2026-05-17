"""DESi v3.81 — epistemic Doppelgaenger probe.

Blind-equivalence clustering of plateau anchor
trajectories. No ablation, no coverage labels, no
class IDs feed back into the clustering. The
v3.79 redundancy class map is consulted only at
metric-readout time (purity, recall).
"""
from __future__ import annotations

from .blind_cluster import (
    ClusterClassMatch, all_blind_metrics,
    cluster_class_matches, cluster_purity,
    cluster_recall, cluster_sizes,
    predicted_cluster_count,
)
from .equivalence import (
    BlindCluster, all_blind_clusters,
    largest_gap_threshold, pairwise_distances,
    plateau_anchor_vectors,
    single_link_cluster,
)
from .report import (
    PURITY_THRESHOLD, V381Report,
    build_blind_equivalence_clusters_artifact,
    build_report,
)


__all__ = [
    "BlindCluster", "ClusterClassMatch",
    "PURITY_THRESHOLD", "V381Report",
    "all_blind_clusters", "all_blind_metrics",
    "build_blind_equivalence_clusters_artifact",
    "build_report",
    "cluster_class_matches", "cluster_purity",
    "cluster_recall", "cluster_sizes",
    "largest_gap_threshold",
    "pairwise_distances",
    "plateau_anchor_vectors",
    "predicted_cluster_count",
    "single_link_cluster",
]
