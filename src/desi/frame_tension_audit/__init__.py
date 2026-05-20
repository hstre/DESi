"""DESi v3.10 frame-tension false-positive audit — read-only over v3.9 + v3.8."""
from __future__ import annotations

from .clusters import (
    ClusterSummary,
    MIN_PATCHABLE_SIZE,
    TensionCluster,
    build_clusters,
    summarise_clusters,
)
from .contamination import (
    ContaminationResult,
    probe_all_clusters,
    probe_cluster,
)
from .enums import TensionAuditClass, TensionFailureCause
from .extractor import TensionTarget, extract_tension_targets
from .report import (
    MIN_TENSION_PRECISION_FOR_PATCH,
    PatchabilityVerdict,
    TensionAuditReport,
    TensionMetrics,
    build_tension_audit_report,
)
from .splitter import TensionAuditOutcome, split_tension_targets

__all__ = [
    "ClusterSummary",
    "ContaminationResult",
    "MIN_PATCHABLE_SIZE",
    "MIN_TENSION_PRECISION_FOR_PATCH",
    "PatchabilityVerdict",
    "TensionAuditClass",
    "TensionAuditOutcome",
    "TensionAuditReport",
    "TensionCluster",
    "TensionFailureCause",
    "TensionMetrics",
    "TensionTarget",
    "build_clusters",
    "build_tension_audit_report",
    "extract_tension_targets",
    "probe_all_clusters",
    "probe_cluster",
    "split_tension_targets",
    "summarise_clusters",
]
