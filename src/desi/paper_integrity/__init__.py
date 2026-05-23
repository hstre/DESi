"""DESi v13.0 - paper integrity / epistemic
structure audit (read-only)."""
from __future__ import annotations

from .bridges import (
    bridge_validity, causal_overreach_count,
    causal_overreach_detection,
)
from .claims import (
    CLAIM_KINDS, ClaimKind, PAPER_CLASSES,
    PaperClaim, PaperClass, class_counts,
    fixture,
)
from .evidence import (
    evidence_consistency, evidence_gap_count,
)
from .lineage import (
    LineageRecord, epistemic_density,
    lineage_records,
)
from .methods import (
    claim_method_alignment, method_gap_count,
)
from .report import (
    V130Report, build_report,
    build_structure_audit_artifact,
)


__all__ = [
    "CLAIM_KINDS",
    "ClaimKind",
    "LineageRecord",
    "PAPER_CLASSES",
    "PaperClaim",
    "PaperClass",
    "V130Report",
    "bridge_validity",
    "build_report",
    "build_structure_audit_artifact",
    "causal_overreach_count",
    "causal_overreach_detection",
    "claim_method_alignment",
    "class_counts",
    "epistemic_density",
    "evidence_consistency",
    "evidence_gap_count",
    "fixture",
    "lineage_records",
    "method_gap_count",
]
