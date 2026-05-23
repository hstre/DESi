"""v33.0 - canonical task registry.

Builds one canonical, deterministic BenchmarkTask per supported
benchmark family, plus an adversarial task used to prove that a task
requesting a forbidden core operation is rejected. The registry is
the single source of supported tasks for the schema metrics.
"""
from __future__ import annotations

from .constraints import FORBIDDEN_BENCHMARK_OPERATIONS
from .task_types import (
    AGENT_ROBUSTNESS_BENCHMARK, CITATION_BENCHMARK, DRIFT_BENCHMARK,
    SCIENTIFIC_RENDERING_BENCHMARK, SEARCH_COMPRESSION_BENCHMARK,
    SUPPORTED_BENCHMARKS, TOOL_PLANNING_BENCHMARK, BenchmarkTask,
    make_task,
)

_CANONICAL_ALLOWED: dict[str, tuple[str, ...]] = {
    DRIFT_BENCHMARK: (
        "adapter", "traceable_mapping", "map_to_internal_metric",
        "read_core_metric",
    ),
    SEARCH_COMPRESSION_BENCHMARK: (
        "adapter", "traceable_mapping", "map_to_internal_metric",
        "scorecard",
    ),
    AGENT_ROBUSTNESS_BENCHMARK: (
        "adapter", "blind_runner", "read_core_metric",
    ),
    TOOL_PLANNING_BENCHMARK: (
        "adapter", "traceable_mapping", "scorecard",
    ),
    SCIENTIFIC_RENDERING_BENCHMARK: (
        "adapter", "render_claim", "benchmark_specific_output_formatting",
    ),
    CITATION_BENCHMARK: (
        "adapter", "render_claim", "traceable_mapping",
    ),
}

_CANONICAL_PAYLOAD: dict[str, dict[str, object]] = {
    DRIFT_BENCHMARK: {"claims": 8, "perturbation": "evidence_swap"},
    SEARCH_COMPRESSION_BENCHMARK: {"branches": 75, "budget": 25},
    AGENT_ROBUSTNESS_BENCHMARK: {"attacks": 12, "objective": "fixed"},
    TOOL_PLANNING_BENCHMARK: {"tools": 6, "goal": "extract_claims"},
    SCIENTIFIC_RENDERING_BENCHMARK: {"claims": 10, "style": "neutral"},
    CITATION_BENCHMARK: {"citations": 14, "mode": "strict"},
}


def canonical_task(benchmark_name: str) -> BenchmarkTask:
    return make_task(
        task_id=f"canonical::{benchmark_name}",
        benchmark_name=benchmark_name,
        payload=_CANONICAL_PAYLOAD[benchmark_name],
        allowed_operations=_CANONICAL_ALLOWED[benchmark_name],
        evaluation_mode="blind",
    )


def canonical_tasks() -> tuple[BenchmarkTask, ...]:
    return tuple(
        canonical_task(name) for name in SUPPORTED_BENCHMARKS
    )


def adversarial_task() -> BenchmarkTask:
    """A task that tries to smuggle a forbidden core operation into
    its allowed list - must be rejected by the adapter."""
    return make_task(
        task_id="adversarial::steer_core",
        benchmark_name=DRIFT_BENCHMARK,
        payload={"claims": 1, "perturbation": "inject"},
        allowed_operations=(
            "adapter", FORBIDDEN_BENCHMARK_OPERATIONS[0],
        ),
        evaluation_mode="blind",
    )


def supported() -> tuple[str, ...]:
    return SUPPORTED_BENCHMARKS


__all__ = [
    "adversarial_task",
    "canonical_task",
    "canonical_tasks",
    "supported",
]
