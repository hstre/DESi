"""DESi v3.57 — content vs method feature decomposition.

Partitions the 9-d StateVector schema into a 5-d
content subspace and a 4-d method subspace, builds
per-subspace 1-NN clusters across the v3.50
trajectory universe (20 plateau + 145 leakage), and
measures their pairwise agreement.
"""
from __future__ import annotations

from .decompose import (
    TrajectoryFeatures, cluster_assignments,
    cluster_count, cohort_features,
    cohort_purity, content_method_overlap,
    replay_stability, within_cohort_overlap,
)
from .features import (
    CONTENT_DIMS, METHOD_DIMS, content_state,
    content_vector, method_state, method_vector,
)
from .report import (
    MAX_CONTENT_METHOD_OVERLAP, V357Report,
    build_content_method_decomposition_artifact,
    build_report,
)


__all__ = [
    "CONTENT_DIMS", "MAX_CONTENT_METHOD_OVERLAP",
    "METHOD_DIMS", "TrajectoryFeatures", "V357Report",
    "build_content_method_decomposition_artifact",
    "build_report", "cluster_assignments",
    "cluster_count", "cohort_features",
    "cohort_purity", "content_method_overlap",
    "content_state", "content_vector",
    "method_state", "method_vector",
    "replay_stability", "within_cohort_overlap",
]
