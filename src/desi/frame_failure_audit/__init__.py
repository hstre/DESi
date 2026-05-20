"""DESi v3.6 frame-failure cluster audit — read-only over v3.5."""
from __future__ import annotations

from .classes import FrameFailureClass
from .classifier import classify, classify_all
from .clusters import (
    ClusterSummary,
    FailureCluster,
    FrameBreakdown,
    build_clusters,
    per_frame_breakdown,
)
from .extractor import FrameFailureRecord, extract_failures
from .negative_control import NEGATIVE_CONTROLS, NegativeControlCase
from .patchability import (
    ContaminationProbe,
    PatchabilityVerdict,
    assess_patchability,
    probe_contamination,
)
from .report import (
    FrameFailureAuditReport,
    NegativeControlOutcome,
    build_audit_report,
)

__all__ = [
    "ClusterSummary",
    "ContaminationProbe",
    "FailureCluster",
    "FrameBreakdown",
    "FrameFailureAuditReport",
    "FrameFailureClass",
    "FrameFailureRecord",
    "NEGATIVE_CONTROLS",
    "NegativeControlCase",
    "NegativeControlOutcome",
    "PatchabilityVerdict",
    "assess_patchability",
    "build_audit_report",
    "build_clusters",
    "classify",
    "classify_all",
    "extract_failures",
    "per_frame_breakdown",
    "probe_contamination",
]
