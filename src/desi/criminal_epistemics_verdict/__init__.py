"""DESi v16.4 - Criminal Epistemics Verdict
(Kennedy epistemics sandbox, read-only).

Aggregates v16.0-v16.3 into five directive metrics,
a closed A-E taxonomy, and a six-condition concept
gate. Answers the Killerfrage: can an epistemic
system analyse a historical criminal case without
becoming a truth machine? DESi claims no narrative
authority and makes no new factual claim.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, GateCondition, aggregate,
    class_rank, classify_corpus,
    conflict_cluster_count, epistemic_integrity,
    gate_conditions, gate_failing_conditions,
    gate_passes_all, speculation_resistance,
)
from .report import (
    PHASE_VERDICTS, VERDICT_HALT, VERDICT_STRUCTURED,
    VERDICT_UNSTABLE, V164Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    CRIMINAL_EPISTEMICS_CLASSES,
    CriminalEpistemicsClass,
)


__all__ = [
    "CRIMINAL_EPISTEMICS_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "AggregateMetrics",
    "CriminalEpistemicsClass",
    "GateCondition",
    "V164Report",
    "aggregate",
    "class_rank",
    "classify_corpus",
    "conflict_cluster_count",
    "epistemic_integrity",
    "build_report",
    "build_verdict_artifact",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "speculation_resistance",
]
