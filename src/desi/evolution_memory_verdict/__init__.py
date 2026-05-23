"""DESi v30.4 - Evolution Memory Verdict (read-only).

Aggregates one signal per dimension from the v30.0-v30.3 layers,
checks the six-condition Concept Gate (replay integrity,
governance preservation, lineage integrity, risk visibility,
human-approval enforcement, evolution traceability), and
classifies the evolution memory on a closed A-E taxonomy. The
goal is replay-validated evolutionary memory under human
governance - never autonomous optimisation dynamics.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, EvolutionMetrics,
    GateCondition, aggregate, classify_corpus,
    evolution_traceability, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_preservation, human_approval_enforcement,
    lineage_integrity, replay_integrity, replay_stability,
    risk_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GOVERNED, VERDICT_HALT,
    VERDICT_UNSTABLE, V304Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    EVOLUTION_CLASSES, EvolutionClass, class_meaning,
    class_rank, is_acceptable,
)


__all__ = [
    "EVOLUTION_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "EvolutionClass",
    "EvolutionMetrics",
    "GateCondition",
    "V304Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "evolution_traceability",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_preservation",
    "human_approval_enforcement",
    "is_acceptable",
    "lineage_integrity",
    "replay_integrity",
    "replay_stability",
    "risk_visibility",
]
