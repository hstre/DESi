"""DESi v32.4 - Evolution Benchmark Verdict (read-only).

Final verdict on the longitudinal evolution benchmark
DESi_baseline_frozen_v1 vs DESi_mutated_v31. Aggregates one signal
per dimension from the v32.0-v32.3 layers, checks a six-condition
Concept Gate and classifies on a closed A-E taxonomy. The benchmark
is real and measured, blind-evaluated, byte-identical,
governance-identical and replay-stable; human approval is mandatory.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, BenchmarkMetrics,
    GateCondition, aggregate, artifact_identity, blind_validation,
    classify_corpus, evolution_traceability, gate_conditions,
    gate_failing_conditions, gate_passes_all, governance_identity,
    human_approval_enforcement, measured_evolutionary_improvement,
    replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_UNVALIDATED,
    VERDICT_VALIDATED, V324Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    BENCHMARK_CLASSES, BenchmarkClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "BENCHMARK_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_UNVALIDATED",
    "VERDICT_VALIDATED",
    "BenchmarkClass",
    "BenchmarkMetrics",
    "GateCondition",
    "V324Report",
    "aggregate",
    "artifact_identity",
    "blind_validation",
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
    "governance_identity",
    "human_approval_enforcement",
    "is_acceptable",
    "measured_evolutionary_improvement",
    "replay_stability",
]
