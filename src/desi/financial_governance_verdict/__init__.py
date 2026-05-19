"""DESi v15.4 - Financial Governance Verdict (DAX
retrospective, read-only).

Aggregates v15.0-v15.3 into the five directive
metrics, a closed A-E governance taxonomy, and the
six-condition concept gate. Answers the phase
Killerfrage: can an epistemic system structure
financial audit without becoming a rating machine?
Never concludes fraud, never rates, never advises.
Post-hoc outcomes are validation labels only.
"""
from __future__ import annotations

from .classification import (
    GATE_PASS_STATEMENT, AggregateMetrics,
    GateCondition, aggregate,
    audit_priority_quality, class_histogram,
    corpus_class, epistemic_transparency,
    false_accusation_rate, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_integrity,
)
from .report import (
    PHASE_VERDICTS, VERDICT_HALT,
    VERDICT_STRUCTURED, VERDICT_UNRESOLVED,
    FirmGovernanceVerdict, V154Report,
    build_report, build_verdict_artifact,
    firm_governance_verdicts,
)
from .taxonomy import (
    GOVERNANCE_CLASSES, GovernanceClass,
    class_rank, classify_firm, firm_classes,
)


__all__ = [
    "GATE_PASS_STATEMENT",
    "GOVERNANCE_CLASSES",
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNRESOLVED",
    "AggregateMetrics",
    "FirmGovernanceVerdict",
    "GateCondition",
    "GovernanceClass",
    "V154Report",
    "aggregate",
    "audit_priority_quality",
    "build_report",
    "build_verdict_artifact",
    "class_histogram",
    "class_rank",
    "classify_firm",
    "corpus_class",
    "epistemic_transparency",
    "false_accusation_rate",
    "firm_classes",
    "firm_governance_verdicts",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_integrity",
]
