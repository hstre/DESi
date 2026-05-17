"""DESi v3.38 — plateau vs. unexpected-rescue separation.

Geometric audit: can DESi tell its intended targets
apart from its accidental rescues?
"""
from __future__ import annotations

from .boundary import (
    FeatureSplit, PLATEAU_LABEL, RESCUE_LABEL,
    all_feature_splits, best_separating_split,
    best_split_for_feature, support_final_split,
)
from .clustering import (
    ClusterAssignment, assign_clusters,
    connected_components, one_nn_edges,
)
from .distance import (
    PairwiseDistance, euclidean, overlap_rate,
    pairwise_distances, per_state_value,
    trajectory_vector,
)
from .report import (
    MIN_SEPARABILITY, V338Report, build_report,
    build_separability_map_artifact,
    build_separation_artifact,
)


__all__ = [
    "ClusterAssignment", "FeatureSplit",
    "MIN_SEPARABILITY", "PLATEAU_LABEL",
    "PairwiseDistance", "RESCUE_LABEL", "V338Report",
    "all_feature_splits", "assign_clusters",
    "best_separating_split", "best_split_for_feature",
    "build_report", "build_separability_map_artifact",
    "build_separation_artifact", "connected_components",
    "euclidean", "one_nn_edges", "overlap_rate",
    "pairwise_distances", "per_state_value",
    "support_final_split", "trajectory_vector",
]
