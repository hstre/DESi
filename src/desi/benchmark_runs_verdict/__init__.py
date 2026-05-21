"""DESi v34.4 - External Benchmark Verdict (read-only).

Final verdict on the external benchmark runs. Aggregates one score
per family from the v34.0-v34.3 runs, checks a six-condition Concept
Gate and classifies on a closed A-E taxonomy. DESi was tested against
drift, search compression, reproducibility and scientific rendering
without changing its epistemic core or replay - tested by benchmarks,
not steered.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, BenchmarkRunMetrics,
    GateCondition, aggregate, classify_corpus, core_identity,
    drift_benchmark_score, gate_conditions, gate_failing_conditions,
    gate_passes_all, reproducibility_score, replay_stability,
    scientific_rendering_score, search_compression_score,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PASSED,
    VERDICT_UNVALIDATED, V344Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    BENCHMARK_RUN_CLASSES, BenchmarkRunClass, class_meaning,
    class_rank, is_acceptable,
)


__all__ = [
    "BENCHMARK_RUN_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "BenchmarkRunClass",
    "BenchmarkRunMetrics",
    "GateCondition",
    "V344Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "core_identity",
    "drift_benchmark_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "is_acceptable",
    "replay_stability",
    "reproducibility_score",
    "scientific_rendering_score",
    "search_compression_score",
]
