"""DESi v3.91 — frame-normalized minimal features.

Tests the v3.82 proxy {branch_cost,
contradiction_load} and its alternatives on the
v3.89 residual projection of the novel anchor
pool.
"""
from __future__ import annotations

from .ablation import (
    FeatureSubsetOutcome,
    best_minimal_feature_set,
    informative_subset_outcomes,
    marginal_frame_gain,
    normalized_predictive_auc,
    normalized_proxy_accuracy,
)
from .minimal import (
    PROXY_DIMS,
    cluster_residual,
    no_frame_projection,
    residual_full,
    residual_projection,
)
from .report import (
    PROXY_THRESHOLD,
    V391Report,
    build_frame_normalized_minimal_features_artifact,
    build_report,
)


__all__ = [
    "FeatureSubsetOutcome",
    "PROXY_DIMS", "PROXY_THRESHOLD",
    "V391Report",
    "best_minimal_feature_set",
    "build_frame_normalized_minimal_features_artifact",
    "build_report",
    "cluster_residual",
    "informative_subset_outcomes",
    "marginal_frame_gain",
    "no_frame_projection",
    "normalized_predictive_auc",
    "normalized_proxy_accuracy",
    "residual_full",
    "residual_projection",
]
