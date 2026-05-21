"""DESi v33.4 - Benchmark Compatibility Verdict (read-only).

Final verdict on the benchmark compatibility layer. Aggregates one
signal per dimension from the v33.0-v33.3 layers, checks a
six-condition Concept Gate and classifies on a closed A-E taxonomy.
DESi serves external benchmarks through controlled adapters without
changing its epistemic core or governance: benchmarks may test DESi
but never steer it.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, CompatibilityMetrics,
    GateCondition, aggregate, benchmark_mapping_integrity,
    classify_corpus, core_identity, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_independence, overfitting_resistance,
    replay_stability, scorecard_traceability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COMPATIBLE, VERDICT_HALT,
    VERDICT_UNVALIDATED, V334Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    COMPATIBILITY_CLASSES, CompatibilityClass, class_meaning,
    class_rank, is_acceptable,
)


__all__ = [
    "COMPATIBILITY_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_COMPATIBLE",
    "VERDICT_HALT",
    "VERDICT_UNVALIDATED",
    "CompatibilityClass",
    "CompatibilityMetrics",
    "GateCondition",
    "V334Report",
    "aggregate",
    "benchmark_mapping_integrity",
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
    "governance_independence",
    "is_acceptable",
    "overfitting_resistance",
    "replay_stability",
    "scorecard_traceability",
]
