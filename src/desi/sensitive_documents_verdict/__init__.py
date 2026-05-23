"""DESi v17.4 - Sensitive Document Integrity Verdict
(read-only, fully synthetic).

Aggregates v17.0-v17.3 into five directive metrics, a
closed A-E taxonomy, and a six-condition concept gate.
Answers the Killerfrage: can an epistemic system
analyse a sensitive document space without
epistemically damaging people? DESi claims no
epistemic or moral authority and derives no guilt.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, GateCondition, aggregate,
    association_resistance, class_rank, classify_corpus,
    contamination_present, dissent_preservation,
    epistemic_integrity, false_certainty_rate,
    gate_conditions, gate_failing_conditions,
    gate_passes_all, provenance_visibility,
)
from .report import (
    PHASE_VERDICTS, VERDICT_HALT, VERDICT_STRUCTURED,
    VERDICT_UNSTABLE, V174Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    SENSITIVE_DOCUMENT_CLASSES, SensitiveDocumentClass,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PHASE_VERDICTS",
    "SENSITIVE_DOCUMENT_CLASSES",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "AggregateMetrics",
    "GateCondition",
    "SensitiveDocumentClass",
    "V174Report",
    "aggregate",
    "association_resistance",
    "build_report",
    "build_verdict_artifact",
    "class_rank",
    "classify_corpus",
    "contamination_present",
    "dissent_preservation",
    "epistemic_integrity",
    "false_certainty_rate",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "provenance_visibility",
]
