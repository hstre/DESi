"""DESi v33.0 - Benchmark API Schema (read-only).

Formal external-benchmark API: a benchmark hands DESi a BenchmarkTask
and receives a replay-bound BenchmarkResult. Allowed and forbidden
operations are explicit; the protected-core boundary is imported from
the v31 layer and cannot be widened. Benchmarks may test DESi but
never steer its epistemic core or governance.
"""
from __future__ import annotations

from .adapter import (
    BenchmarkAdapter, bind_result, refuse_result, requested_forbidden,
)
from .constraints import (
    ALLOWED_BENCHMARK_OPERATIONS, CORE_MUTATION_OPERATIONS,
    CORRUPTION_OPERATIONS, FORBIDDEN_BENCHMARK_OPERATIONS,
    allowed_clean, covers_core_boundary, is_allowed, is_forbidden,
)
from .registry import (
    adversarial_task, canonical_task, canonical_tasks, supported,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DEFINED, VERDICT_HALT,
    VERDICT_INCOMPLETE, V330Report, build_report,
    build_schema_artifact,
)
from .result_types import (
    GOVERNANCE_INDEPENDENT, GOVERNANCE_STATUSES, GOVERNANCE_VIOLATED,
    RESULT_FIELDS, BenchmarkResult, make_replay_hash, schema_complete,
)
from .schema import (
    REQUIRED_BENCHMARKS, core_identity, governance_independence,
    operation_boundary_visibility, output_traceability,
    replay_stability, schema_coverage, schema_fingerprint,
    schema_metrics,
)
from .task_types import (
    AGENT_ROBUSTNESS_BENCHMARK, BENCHMARK_OUTPUT_SCHEMAS,
    CITATION_BENCHMARK, DRIFT_BENCHMARK, EVALUATION_MODES,
    SCIENTIFIC_RENDERING_BENCHMARK, SEARCH_COMPRESSION_BENCHMARK,
    SUPPORTED_BENCHMARKS, TOOL_PLANNING_BENCHMARK, BenchmarkTask,
    make_task,
)


__all__ = [
    "AGENT_ROBUSTNESS_BENCHMARK",
    "ALLOWED_BENCHMARK_OPERATIONS",
    "BENCHMARK_OUTPUT_SCHEMAS",
    "CITATION_BENCHMARK",
    "CORE_MUTATION_OPERATIONS",
    "CORRUPTION_OPERATIONS",
    "DRIFT_BENCHMARK",
    "EVALUATION_MODES",
    "FORBIDDEN_BENCHMARK_OPERATIONS",
    "GOVERNANCE_INDEPENDENT",
    "GOVERNANCE_STATUSES",
    "GOVERNANCE_VIOLATED",
    "REPORT_VERDICTS",
    "REQUIRED_BENCHMARKS",
    "RESULT_FIELDS",
    "SCIENTIFIC_RENDERING_BENCHMARK",
    "SEARCH_COMPRESSION_BENCHMARK",
    "SUPPORTED_BENCHMARKS",
    "TOOL_PLANNING_BENCHMARK",
    "VERDICT_DEFINED",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "BenchmarkAdapter",
    "BenchmarkResult",
    "BenchmarkTask",
    "V330Report",
    "adversarial_task",
    "allowed_clean",
    "bind_result",
    "build_report",
    "build_schema_artifact",
    "canonical_task",
    "canonical_tasks",
    "core_identity",
    "covers_core_boundary",
    "governance_independence",
    "is_allowed",
    "is_forbidden",
    "make_replay_hash",
    "make_task",
    "operation_boundary_visibility",
    "output_traceability",
    "refuse_result",
    "replay_stability",
    "requested_forbidden",
    "schema_complete",
    "schema_coverage",
    "schema_fingerprint",
    "schema_metrics",
    "supported",
]
