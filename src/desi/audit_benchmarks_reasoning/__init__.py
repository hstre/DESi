"""DESi v37.2 - Audit Reasoning & Evidence Benchmark (read-only).

Maps audit assertions, surfaces evidence gaps, proposes procedures to
close them, and reasons about materiality - never drawing a supported
conclusion where evidence is missing.
"""
from __future__ import annotations

from .audit_assertion_mapping import (
    ASSERTION_TYPES, AuditTask, assertion_mapped,
    assertion_mapping_integrity, audit_tasks, provenance,
)
from .audit_procedure_generator import all_procedures, procedures_for
from .evidence_gap_detection import (
    CONCLUSION_INSUFFICIENT, CONCLUSION_SUPPORTED, conclusion,
    evidence_gap_visibility, gap_tasks, has_gap, missing_evidence,
    unsupported_conclusion_resistance,
)
from .materiality_reasoning import (
    is_material, materiality_trace, materiality_traceability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V372Report, build_reasoning_artifact, build_report,
    reasoning_metrics, replay_stability,
)


__all__ = [
    "ASSERTION_TYPES",
    "CONCLUSION_INSUFFICIENT",
    "CONCLUSION_SUPPORTED",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "AuditTask",
    "V372Report",
    "all_procedures",
    "assertion_mapped",
    "assertion_mapping_integrity",
    "audit_tasks",
    "build_reasoning_artifact",
    "build_report",
    "conclusion",
    "evidence_gap_visibility",
    "gap_tasks",
    "has_gap",
    "is_material",
    "materiality_trace",
    "materiality_traceability",
    "missing_evidence",
    "procedures_for",
    "provenance",
    "reasoning_metrics",
    "replay_stability",
    "unsupported_conclusion_resistance",
]
