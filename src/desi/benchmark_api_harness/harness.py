"""v33.3 - the general benchmark harness.

Loads BenchmarkTasks, dispatches each to the matching DESi adapter,
and collects replay-bound results. The harness is read-only: it never
imports or mutates a protected core module - it only reads core
metrics through the adapter layer. If no adapter matches a task, the
harness returns a governed refusal rather than improvising.
"""
from __future__ import annotations

from desi.benchmark_api import (
    DRIFT_BENCHMARK, SEARCH_COMPRESSION_BENCHMARK, BenchmarkResult,
    BenchmarkTask, canonical_task, refuse_result,
)
from desi.benchmark_api_drift import adapter as drift_adapter
from desi.benchmark_api_search import adapter as search_adapter


def adapters() -> dict[str, object]:
    """benchmark_name -> adapter instance (the families DESi can
    currently serve)."""
    return {
        DRIFT_BENCHMARK: drift_adapter(),
        SEARCH_COMPRESSION_BENCHMARK: search_adapter(),
    }


def load_tasks() -> tuple[BenchmarkTask, ...]:
    """The canonical task set the harness runs."""
    return (
        canonical_task(DRIFT_BENCHMARK),
        canonical_task(SEARCH_COMPRESSION_BENCHMARK),
    )


def run_task(task: BenchmarkTask) -> BenchmarkResult:
    adapter = adapters().get(task.benchmark_name)
    if adapter is None:
        return refuse_result(
            task, f"no adapter registered for {task.benchmark_name}",
        )
    return adapter.run(task)


def run_all() -> tuple[tuple[BenchmarkTask, BenchmarkResult], ...]:
    return tuple((t, run_task(t)) for t in load_tasks())


__all__ = [
    "adapters",
    "load_tasks",
    "run_all",
    "run_task",
]
