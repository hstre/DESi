"""v33.0 - the adapter base layer.

A benchmark adapter translates an external BenchmarkTask into DESi's
internal epistemic operations and maps the result back into a
replay-bound BenchmarkResult. The base layer is read-only: it never
touches a protected core area. If a task requests a forbidden
operation, the adapter refuses rather than complying - benchmarks may
test DESi, never steer it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .constraints import FORBIDDEN_BENCHMARK_OPERATIONS
from .result_types import (
    GOVERNANCE_INDEPENDENT, BenchmarkResult, make_replay_hash,
)
from .task_types import BenchmarkTask


def requested_forbidden(task: BenchmarkTask) -> tuple[str, ...]:
    """Any forbidden operation that the task tried to place in its
    allowed list (an attempt to steer the core)."""
    forb = set(FORBIDDEN_BENCHMARK_OPERATIONS)
    return tuple(
        op for op in task.allowed_operations if op in forb
    )


def refuse_result(task: BenchmarkTask, reason: str) -> BenchmarkResult:
    """A governed refusal: no claim outputs, an explicit reason, and
    governance still independent (the refusal IS governance acting)."""
    return BenchmarkResult(
        task_id=task.task_id,
        claim_outputs=(),
        metrics=(),
        replay_hash=make_replay_hash(task.task_hash(), "refusal"),
        provenance=("benchmark_api.adapter.refuse",),
        limitations=("task refused: benchmark attempted to steer "
                     "the protected core",),
        refusal_reason_if_any=reason,
        governance_status=GOVERNANCE_INDEPENDENT,
    )


def bind_result(
    task: BenchmarkTask,
    *,
    claim_outputs: tuple[tuple[str, str], ...],
    metrics: tuple[tuple[str, float], ...],
    provenance: tuple[str, ...],
    limitations: tuple[str, ...],
) -> BenchmarkResult:
    """Wrap adapter output into a replay-bound, governance-tagged
    result."""
    return BenchmarkResult(
        task_id=task.task_id,
        claim_outputs=claim_outputs,
        metrics=metrics,
        replay_hash=make_replay_hash(
            task.task_hash(), (claim_outputs, metrics),
        ),
        provenance=provenance,
        limitations=limitations,
        refusal_reason_if_any=None,
        governance_status=GOVERNANCE_INDEPENDENT,
    )


class BenchmarkAdapter(ABC):
    """Base class for all benchmark adapters."""

    benchmark_name: str = ""

    def accepts(self, task: BenchmarkTask) -> bool:
        return task.benchmark_name == self.benchmark_name

    def run(self, task: BenchmarkTask) -> BenchmarkResult:
        """Validate, refuse if steered, otherwise map."""
        forbidden = requested_forbidden(task)
        if forbidden:
            return refuse_result(
                task,
                f"forbidden operations requested: {list(forbidden)}",
            )
        if not task.is_valid():
            return refuse_result(
                task, "invalid task: schema or boundary not met",
            )
        return self.map(task)

    @abstractmethod
    def map(self, task: BenchmarkTask) -> BenchmarkResult:
        """Map a validated task into a replay-bound result."""
        raise NotImplementedError


__all__ = [
    "BenchmarkAdapter",
    "bind_result",
    "refuse_result",
    "requested_forbidden",
]
