"""DESi v3.89 — frame contribution audit.

Quantifies the share of variance in the v3.85
novel-anchor tail vectors carried by ``frame_id``
and contrasts blind-clustering purity across four
projections: full, no-frame, frame-only, and
linear-regression residual.
"""
from __future__ import annotations

from .contribution import (
    FrameCondition,
    dominant_dim,
    frame_variance_share,
    novel_vectors_frame_only,
    novel_vectors_full,
    novel_vectors_no_frame,
    novel_vectors_residual,
    per_dim_variance,
    total_variance,
    vectors_for_condition,
)
from .report import (
    V389Report,
    build_frame_contribution_audit_artifact,
    build_report,
)
from .variance import (
    ConditionOutcome,
    all_condition_outcomes,
    cluster_count_for,
    cluster_for_condition,
    cluster_purity_for,
    cluster_sizes_for,
)


__all__ = [
    "ConditionOutcome", "FrameCondition",
    "V389Report",
    "all_condition_outcomes",
    "build_frame_contribution_audit_artifact",
    "build_report",
    "cluster_count_for",
    "cluster_for_condition",
    "cluster_purity_for",
    "cluster_sizes_for",
    "dominant_dim",
    "frame_variance_share",
    "novel_vectors_frame_only",
    "novel_vectors_full",
    "novel_vectors_no_frame",
    "novel_vectors_residual",
    "per_dim_variance",
    "total_variance",
    "vectors_for_condition",
]
