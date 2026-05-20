"""DESi v3.96 — entanglement resolution attempt on
the entangled (G_v316susp + E_v317h) pair using the
frame-normalized residual space plus per-anchor
temporal rise indices.
"""
from __future__ import annotations

from .predict import (
    MAX_SEARCH_SIZE,
    ResolutionOutcome,
    all_resolution_outcomes,
    auc_for,
    baseline_frame_normalized_auc,
    baseline_frame_normalized_fpr,
    best_feature_set, best_outcome,
    cluster_for, fpr_for,
    purity_for, resolved_auc,
    resolved_fpr, resolved_purity,
)
from .report import (
    AUC_THRESHOLD, PURITY_THRESHOLD,
    V396Report,
    build_entangled_resolution_artifact,
    build_report,
)
from .resolve import (
    FeatureSpec, RESIDUAL_DIMS,
    TEMPORAL_DIMS, feature_vector,
    feature_vector_for_spec,
)


__all__ = [
    "AUC_THRESHOLD",
    "FeatureSpec",
    "MAX_SEARCH_SIZE",
    "PURITY_THRESHOLD",
    "RESIDUAL_DIMS",
    "ResolutionOutcome",
    "TEMPORAL_DIMS",
    "V396Report",
    "all_resolution_outcomes",
    "auc_for",
    "baseline_frame_normalized_auc",
    "baseline_frame_normalized_fpr",
    "best_feature_set", "best_outcome",
    "build_entangled_resolution_artifact",
    "build_report",
    "cluster_for",
    "feature_vector",
    "feature_vector_for_spec",
    "fpr_for", "purity_for",
    "resolved_auc", "resolved_fpr",
    "resolved_purity",
]
