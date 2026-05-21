"""DESi v35.4 - Real External Benchmark Verdict (read-only).

Final verdict on the real external benchmark runs. Aggregates one
score per dimension from the v35.0-v35.3 layers, checks a six-condition
Concept Gate and classifies on a closed A-E taxonomy. DESi was tested
against connector-loaded drift and search datasets without changing
its epistemic core or governance - tested by benchmarks, not steered.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    RealBenchmarkMetrics, aggregate, classify_corpus, core_identity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_stability, real_drift_score, real_search_score,
    replay_stability, reproducibility_score,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PASSED,
    VERDICT_UNVALIDATED, V354Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    REAL_BENCHMARK_CLASSES, RealBenchmarkClass, class_meaning,
    class_rank, is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REAL_BENCHMARK_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "GateCondition",
    "RealBenchmarkClass",
    "RealBenchmarkMetrics",
    "V354Report",
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
    "governance_stability",
    "is_acceptable",
    "real_drift_score",
    "real_search_score",
    "replay_stability",
    "reproducibility_score",
]
