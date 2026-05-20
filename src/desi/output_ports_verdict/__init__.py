"""DESi v25.4 - Output Port Verdict (read-only).

Aggregates one signal per dimension from the v25.0-v25.3 layers,
checks the six-condition Concept Gate, and classifies DESi's
scientific output ports on a closed A-E taxonomy. The verdict
confirms whether DESi produces scientific documents as citeable,
graph-bound, replay-stable output ports - exporting epistemic
graphs into document formats rather than writing papers.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    PortMetrics, aggregate, citation_integrity, classify_corpus,
    cross_port_consistency, gate_conditions,
    gate_failing_conditions, gate_passes_all, no_naked_claims,
    port_schema_integrity, replay_stability, result_traceability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PUBLISHABLE,
    VERDICT_UNSTABLE, V254Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    PORT_CLASSES, PortClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PORT_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PUBLISHABLE",
    "VERDICT_UNSTABLE",
    "GateCondition",
    "PortClass",
    "PortMetrics",
    "V254Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "citation_integrity",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "cross_port_consistency",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "is_acceptable",
    "no_naked_claims",
    "port_schema_integrity",
    "replay_stability",
    "result_traceability",
]
