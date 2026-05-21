"""DESi v31.4 - Peripheral Mutation Verdict (read-only).

Final verdict on the controlled peripheral mutation branch.
Aggregates one signal per dimension from the v31.0-v31.3 layers,
checks a six-condition Concept Gate and classifies on a closed A-E
taxonomy. Every mutation is a real, branch-isolated code change
outside the protected core; the protected core stays byte-identical,
governance is unchanged, mutations are traceable and replay-stable,
and nothing is merged. Human approval is mandatory.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    MutationMetrics, aggregate, classify_corpus, core_identity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_identity, human_approval_enforcement,
    lineage_integrity, mutation_traceability, regression_survival,
    replay_integrity, replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_UNSTABLE,
    VERDICT_VALIDATED, V314Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    MUTATION_CLASSES, MutationClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "MUTATION_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "VERDICT_VALIDATED",
    "GateCondition",
    "MutationClass",
    "MutationMetrics",
    "V314Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "core_identity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "human_approval_enforcement",
    "is_acceptable",
    "lineage_integrity",
    "mutation_traceability",
    "regression_survival",
    "replay_integrity",
    "replay_stability",
]
