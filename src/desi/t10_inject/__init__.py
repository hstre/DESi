"""DESi v3.102 - T10 single-dimension injection."""
from __future__ import annotations

from .inject import (
    baseline_dim, injected_dim,
    injected_vectors, selected_candidate,
)
from .recover import (
    all_injected_clusters, cluster_delta,
    geometry_delta, injected_auc,
    injected_cluster_count,
    injected_cluster_sizes,
    injected_purity,
)
from .report import (
    AUC_THRESHOLD,
    GEOMETRY_DELTA_TOLERANCE,
    PURITY_THRESHOLD,
    V3102Report,
    build_report,
    build_t10_single_dimension_injection_artifact,
)


__all__ = [
    "AUC_THRESHOLD",
    "GEOMETRY_DELTA_TOLERANCE",
    "PURITY_THRESHOLD",
    "V3102Report",
    "all_injected_clusters",
    "baseline_dim",
    "build_report",
    "build_t10_single_dimension_injection_artifact",
    "cluster_delta",
    "geometry_delta",
    "injected_auc",
    "injected_cluster_count",
    "injected_cluster_sizes",
    "injected_dim",
    "injected_purity",
    "injected_vectors",
    "selected_candidate",
]
