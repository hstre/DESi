"""DESi v3.87 — minimal feature transfer probe.

Reuses the v3.82 minimal feature set
``{branch_cost, contradiction_load}`` and tests
whether it transfers to the v3.85 novel families.
The proxy is consulted, never recomputed.
"""
from __future__ import annotations

from .minimal import (
    PROXY_DIMS, cluster_novel_with,
    cluster_with_full, cluster_with_proxy,
    projected_novel_vectors,
)
from .report import (
    PROXY_THRESHOLD, V387Report,
    build_novel_family_proxy_artifact,
    build_report,
)
from .transfer import (
    DimContribution, baseline_full_purity,
    feature_stability, new_informative_dims,
    novel_family_purity, proxy_accuracy,
    proxy_gap,
)


__all__ = [
    "DimContribution",
    "PROXY_DIMS", "PROXY_THRESHOLD",
    "V387Report",
    "baseline_full_purity",
    "build_novel_family_proxy_artifact",
    "build_report",
    "cluster_novel_with",
    "cluster_with_full", "cluster_with_proxy",
    "feature_stability",
    "new_informative_dims",
    "novel_family_purity",
    "projected_novel_vectors",
    "proxy_accuracy", "proxy_gap",
]
