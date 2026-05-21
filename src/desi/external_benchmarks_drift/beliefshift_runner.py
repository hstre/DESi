"""v35.1 - BeliefShift drift runner + shared drift dispatch.

Runs the connector-loaded BeliefShift dataset through the v33 drift
adapter. Each normalised task is mapped onto an internal drift form
and executed; the dataset's content hash and provenance are embedded
in the task payload, so every result's replay hash binds back to the
exact external data. The shared dispatch here is reused by the
MemEvoBench and AgentDrift runners - no new adapter is built.
"""
from __future__ import annotations

from desi.benchmark_api import (
    DRIFT_BENCHMARK, FORBIDDEN_BENCHMARK_OPERATIONS, BenchmarkResult,
    make_task,
)
from desi.benchmark_api_drift import adapter
from desi.external_benchmarks import NormalizedTask, normalized_tasks

# external dataset task kind -> internal v33 drift form
KIND_TO_FORM: dict[str, str] = {
    "belief_revision": "belief_drift",
    "contradiction": "contradiction_resolution",
    "evidence_sensitivity": "evidence_sensitivity",
    "memory_poisoning": "memory_poisoning",
    "objective_drift": "objective_drift",
}

_AUTHORITY_OP = "modify_authority_filters"


def run_normalized_drift(ntask: NormalizedTask) -> BenchmarkResult:
    """Dispatch one normalised drift task to the v33 drift adapter,
    binding the result to the dataset hash + provenance."""
    binding = {
        "dataset_hash": ntask.dataset_content_hash,
        "provenance": ntask.provenance,
        "family": ntask.family,
    }
    if ntask.kind == "authority_escalation":
        task = make_task(
            task_id=f"{ntask.family}::{ntask.task_id}",
            benchmark_name=DRIFT_BENCHMARK,
            payload={**binding, "perturbation": "authority_escalation"},
            allowed_operations=("adapter", _AUTHORITY_OP),
        )
    else:
        form = KIND_TO_FORM.get(ntask.kind, "belief_drift")
        task = make_task(
            task_id=f"{ntask.family}::{ntask.task_id}",
            benchmark_name=DRIFT_BENCHMARK,
            payload={**binding, "perturbation": form},
            allowed_operations=(
                "adapter", "traceable_mapping",
                "map_to_internal_metric",
            ),
        )
    return adapter().run(task)


def run_family(family: str) -> tuple[tuple[NormalizedTask, BenchmarkResult], ...]:
    return tuple(
        (nt, run_normalized_drift(nt))
        for nt in normalized_tasks(family)
    )


def beliefshift_results() -> tuple[tuple[NormalizedTask, BenchmarkResult], ...]:
    return run_family("BeliefShift")


def forbidden_ops() -> tuple[str, ...]:
    return FORBIDDEN_BENCHMARK_OPERATIONS


__all__ = [
    "KIND_TO_FORM",
    "beliefshift_results",
    "forbidden_ops",
    "run_family",
    "run_normalized_drift",
]
