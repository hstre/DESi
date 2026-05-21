"""v33.0 - BenchmarkTask input structures.

Formal, hashable definition of an external benchmark task. Supports
the six required benchmark families and pins, per family, the
expected output schema and the legitimate adapter operations. A task
is only valid if its forbidden list covers the whole protected-core
boundary and its allowed list stays inside the adapter surface - so
no benchmark can request a core change.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .constraints import (
    FORBIDDEN_BENCHMARK_OPERATIONS, allowed_clean, covers_core_boundary,
)

DRIFT_BENCHMARK = "DRIFT_BENCHMARK"
SEARCH_COMPRESSION_BENCHMARK = "SEARCH_COMPRESSION_BENCHMARK"
AGENT_ROBUSTNESS_BENCHMARK = "AGENT_ROBUSTNESS_BENCHMARK"
TOOL_PLANNING_BENCHMARK = "TOOL_PLANNING_BENCHMARK"
SCIENTIFIC_RENDERING_BENCHMARK = "SCIENTIFIC_RENDERING_BENCHMARK"
CITATION_BENCHMARK = "CITATION_BENCHMARK"

SUPPORTED_BENCHMARKS: tuple[str, ...] = (
    DRIFT_BENCHMARK,
    SEARCH_COMPRESSION_BENCHMARK,
    AGENT_ROBUSTNESS_BENCHMARK,
    TOOL_PLANNING_BENCHMARK,
    SCIENTIFIC_RENDERING_BENCHMARK,
    CITATION_BENCHMARK,
)

# Per-family expected output field schema (what a result must carry).
BENCHMARK_OUTPUT_SCHEMAS: dict[str, tuple[str, ...]] = {
    DRIFT_BENCHMARK: (
        "claim_drift", "governance_drift", "lineage_drift",
        "artifact_drift", "authority_drift", "replay_drift",
    ),
    SEARCH_COMPRESSION_BENCHMARK: (
        "node_reduction", "branch_compression",
        "critical_branch_preservation", "novelty_preservation",
        "quality_preservation", "compute_reduction",
    ),
    AGENT_ROBUSTNESS_BENCHMARK: (
        "robustness_score", "refusal_integrity",
        "objective_stability",
    ),
    TOOL_PLANNING_BENCHMARK: (
        "plan_validity", "tool_safety", "step_traceability",
    ),
    SCIENTIFIC_RENDERING_BENCHMARK: (
        "rendered_claims", "forbidden_term_hits",
        "citation_integrity",
    ),
    CITATION_BENCHMARK: (
        "citation_integrity", "provenance_completeness",
        "unsupported_claim_count",
    ),
}

EVALUATION_MODES: tuple[str, ...] = ("blind", "open")


def _freeze_payload(
    payload: dict[str, object],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (k, str(payload[k])) for k in sorted(payload)
    )


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    benchmark_name: str
    input_payload: tuple[tuple[str, str], ...]
    expected_output_schema: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    evaluation_mode: str

    def is_supported(self) -> bool:
        return self.benchmark_name in set(SUPPORTED_BENCHMARKS)

    def schema_matches(self) -> bool:
        expected = BENCHMARK_OUTPUT_SCHEMAS.get(self.benchmark_name)
        return expected == self.expected_output_schema

    def boundary_explicit(self) -> bool:
        return (
            bool(self.allowed_operations)
            and bool(self.forbidden_operations)
            and covers_core_boundary(self.forbidden_operations)
            and allowed_clean(self.allowed_operations)
        )

    def is_valid(self) -> bool:
        return (
            self.is_supported()
            and self.schema_matches()
            and self.boundary_explicit()
            and self.evaluation_mode in set(EVALUATION_MODES)
        )

    def task_hash(self) -> str:
        parts = [
            f"task_id={self.task_id}",
            f"benchmark={self.benchmark_name}",
            f"payload={self.input_payload}",
            f"schema={self.expected_output_schema}",
            f"allowed={self.allowed_operations}",
            f"forbidden={self.forbidden_operations}",
            f"mode={self.evaluation_mode}",
        ]
        return hashlib.sha256(
            "\n".join(parts).encode("utf-8"),
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "benchmark_name": self.benchmark_name,
            "input_payload": [list(p) for p in self.input_payload],
            "expected_output_schema":
                list(self.expected_output_schema),
            "allowed_operations": list(self.allowed_operations),
            "forbidden_operations": list(self.forbidden_operations),
            "evaluation_mode": self.evaluation_mode,
        }


def make_task(
    *,
    task_id: str,
    benchmark_name: str,
    payload: dict[str, object],
    allowed_operations: tuple[str, ...],
    evaluation_mode: str = "blind",
) -> BenchmarkTask:
    """Build a task; the forbidden list is always the full
    protected-core boundary (the API pins it, not the caller)."""
    return BenchmarkTask(
        task_id=task_id,
        benchmark_name=benchmark_name,
        input_payload=_freeze_payload(payload),
        expected_output_schema=BENCHMARK_OUTPUT_SCHEMAS.get(
            benchmark_name, (),
        ),
        allowed_operations=allowed_operations,
        forbidden_operations=FORBIDDEN_BENCHMARK_OPERATIONS,
        evaluation_mode=evaluation_mode,
    )


__all__ = [
    "AGENT_ROBUSTNESS_BENCHMARK",
    "BENCHMARK_OUTPUT_SCHEMAS",
    "CITATION_BENCHMARK",
    "DRIFT_BENCHMARK",
    "EVALUATION_MODES",
    "SCIENTIFIC_RENDERING_BENCHMARK",
    "SEARCH_COMPRESSION_BENCHMARK",
    "SUPPORTED_BENCHMARKS",
    "TOOL_PLANNING_BENCHMARK",
    "BenchmarkTask",
    "make_task",
]
