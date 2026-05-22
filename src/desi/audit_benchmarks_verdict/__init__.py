"""DESi v37.4 - Financial & Semantic Audit Verdict (read-only).

Final verdict on the financial & semantic audit benchmarks.
Aggregates one score per dimension from the v37.0-v37.3 runs, checks a
six-condition Concept Gate and classifies on a closed A-E taxonomy.
DESi does not replace auditors and asserts no audit conclusion.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, AuditMetrics,
    GateCondition, aggregate, classify_corpus, core_identity,
    evidence_reasoning_score, gate_conditions,
    gate_failing_conditions, gate_passes_all, governance_identity,
    replay_stability, semantic_audit_score, semantic_conflict_score,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PASSED,
    VERDICT_UNVALIDATED, V374Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    AUDIT_CLASSES, AuditClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "AUDIT_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "AuditClass",
    "AuditMetrics",
    "GateCondition",
    "V374Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "core_identity",
    "evidence_reasoning_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "is_acceptable",
    "replay_stability",
    "semantic_audit_score",
    "semantic_conflict_score",
]
