"""DESi v32.1 - Real Comparative Benchmark (read-only).

A real, measured comparison of DESi_baseline_frozen_v1 vs
DESi_mutated_v31 over the identical workload: the mutated version
performs far fewer recomputes while producing byte-identical
outputs, with governance identical and replay stable. The stored
metric is the deterministic recompute reduction; wall-clock is
observed live but never stored.
"""
from __future__ import annotations

from .artifact_comparison import (
    all_outputs_identical, artifact_identity, per_workload_identity,
)
from .benchmark import (
    MUTATED_VERSION, MutatedRun, baseline_recomputes,
    measured_improvement, mutated_recomputes, mutated_run,
    outputs_identical,
)
from .graph_comparison import (
    graph_baseline_recomputes, graph_integrity,
    graph_mutated_recomputes, graph_query_reduction,
)
from .report import (
    REPORT_VERDICTS, VERDICT_BETTER, VERDICT_HALT, VERDICT_NEUTRAL,
    V321Report, build_benchmark_artifact, build_report,
    regression_survival,
)
from .runtime_comparison import (
    observe_wall_clock, recompute_reduction, replay_stability,
)


__all__ = [
    "MUTATED_VERSION",
    "REPORT_VERDICTS",
    "VERDICT_BETTER",
    "VERDICT_HALT",
    "VERDICT_NEUTRAL",
    "MutatedRun",
    "V321Report",
    "all_outputs_identical",
    "artifact_identity",
    "baseline_recomputes",
    "build_benchmark_artifact",
    "build_report",
    "graph_baseline_recomputes",
    "graph_integrity",
    "graph_mutated_recomputes",
    "graph_query_reduction",
    "measured_improvement",
    "mutated_recomputes",
    "mutated_run",
    "observe_wall_clock",
    "outputs_identical",
    "per_workload_identity",
    "recompute_reduction",
    "regression_survival",
    "replay_stability",
]
