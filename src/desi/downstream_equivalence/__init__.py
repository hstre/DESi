"""DESi v3.98 - downstream equivalence audit
on the v3.93 entangled (G_v316susp + E_v317h)
pair.
"""
from __future__ import annotations

from .equivalence import (
    AxisOverlap,
    all_axis_overlaps,
    audit_outcome_overlap,
    failure_class_overlap,
    intervention_overlap,
    outcome_divergence,
    path_overlap,
    rescue_eligibility_overlap,
    rollback_overlap,
    verdict_overlap,
)
from .outcomes import (
    AuditOutcome,
    DownstreamSignature,
    FailureClass,
    FinalVerdict,
    InterventionKind,
    all_downstream_signatures,
)
from .report import (
    VERDICT_OVERLAP_THRESHOLD,
    V398Report,
    build_downstream_equivalence_artifact,
    build_report,
)


__all__ = [
    "AuditOutcome", "AxisOverlap",
    "DownstreamSignature",
    "FailureClass", "FinalVerdict",
    "InterventionKind",
    "VERDICT_OVERLAP_THRESHOLD",
    "V398Report",
    "all_axis_overlaps",
    "all_downstream_signatures",
    "audit_outcome_overlap",
    "build_downstream_equivalence_artifact",
    "build_report",
    "failure_class_overlap",
    "intervention_overlap",
    "outcome_divergence",
    "path_overlap",
    "rescue_eligibility_overlap",
    "rollback_overlap",
    "verdict_overlap",
]
