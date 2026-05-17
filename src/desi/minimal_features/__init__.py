"""DESi v3.82 — minimal feature detection.

Probes the 9-dim state vector: which dimensions are
necessary for the v3.81 blind clustering to recover
the v3.79 redundancy class map? Closed 6-condition
ablation enum + greedy backward elimination yields
the minimal proxy feature set.
"""
from __future__ import annotations

from .ablation import (
    AblationOutcome, FeatureAblationKind,
    ablated_vectors, ablation_dim_name,
    all_ablation_outcomes,
    cluster_with_dropped, run_one_ablation,
)
from .importance import (
    FeatureImportance, baseline_purity,
    feature_importance,
    minimal_cluster_accuracy,
    minimal_feature_set, proxy_score,
)
from .report import (
    V382Report,
    build_minimal_feature_detection_artifact,
    build_report,
)


__all__ = [
    "AblationOutcome", "FeatureAblationKind",
    "FeatureImportance", "V382Report",
    "ablated_vectors", "ablation_dim_name",
    "all_ablation_outcomes",
    "baseline_purity",
    "build_minimal_feature_detection_artifact",
    "build_report", "cluster_with_dropped",
    "feature_importance",
    "minimal_cluster_accuracy",
    "minimal_feature_set", "proxy_score",
    "run_one_ablation",
]
