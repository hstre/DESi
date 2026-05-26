"""DESi benchmark ports — PERIPHERAL layer.

The semantic-flow constitution is immutable. Benchmark layers are peripheral.
Benchmarks run ON DESi. Benchmarks do not redefine DESi.

This module is a thin facade over the tested, boundary-enforced benchmark API
(``desi.benchmark_api``). It provides the standardized ports a benchmark needs —
an input port, an output port, an optional pluggable extractor interface, an
optional benchmark runner, and an optional read-only comparison layer — and
nothing else. It adds:

* NO new epistemic ontology and NO new epistemic axes,
* NO new governance and NO new meaning-space architecture,
* NO claim-centric core logic and NO folding/DBA as a core concept.

Every task is built with ``benchmark_api.make_task``, which always pins the full
protected-core forbidden boundary (the caller cannot widen or weaken it), and
every result is produced by a ``benchmark_api.BenchmarkAdapter``, which refuses
any core-mutating operation. Claims appear here only as *projections*
(``claim_outputs``) — they are never the epistemic state space itself.
"""
from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from desi.benchmark_api import (
    BenchmarkAdapter,
    BenchmarkResult,
    BenchmarkTask,
    is_forbidden,
    make_task,
    requested_forbidden,
)

# Re-exported so callers never have to reach past this facade to discover the
# boundary they cannot cross. This is read-only; the facade cannot widen it.
from desi.benchmark_api import FORBIDDEN_BENCHMARK_OPERATIONS


def input_port(
    *,
    task_id: str,
    benchmark_name: str,
    payload: dict[str, object],
    allowed_operations: tuple[str, ...],
    evaluation_mode: str = "blind",
) -> BenchmarkTask:
    """Standardized INPUT port: an external benchmark item becomes a
    boundary-pinned ``BenchmarkTask``. Delegates to ``benchmark_api.make_task``,
    which always attaches the full protected-core forbidden boundary — this
    facade never sets ``forbidden_operations`` itself, so it cannot weaken the
    boundary."""
    return make_task(
        task_id=task_id,
        benchmark_name=benchmark_name,
        payload=payload,
        allowed_operations=allowed_operations,
        evaluation_mode=evaluation_mode,
    )


def output_port(result: BenchmarkResult) -> dict[str, object]:
    """Standardized OUTPUT port: a replay-bound ``BenchmarkResult`` becomes a
    plain, serializable record. Read-only projection of the result the tested
    adapter already produced."""
    return result.to_dict()


@runtime_checkable
class ExtractorPort(Protocol):
    """Optional pluggable EXTRACTOR interface.

    An extractor is a peripheral adapter that turns raw benchmark input into
    claim *projections* — ``(label, value)`` pairs suitable for a task payload
    or a result's ``claim_outputs``. It is explicitly NOT part of the epistemic
    core: it never defines the state space, only feeds projections to it. Any
    P20–P33-style extractor may implement this Protocol to participate as
    benchmark periphery."""

    name: str

    def extract(
        self, payload: dict[str, object]
    ) -> tuple[tuple[str, str], ...]:
        """Return claim projections for the given raw input."""
        ...


class BenchmarkRunner:
    """Optional benchmark RUNNER: pure orchestration over a tested
    ``BenchmarkAdapter``.

    It loops tasks through ``adapter.run`` and collects replay-bound results. It
    holds no epistemic state, performs no projection of its own, and cannot
    touch the core: the adapter refuses any task that requests a forbidden /
    core-mutating operation, so a runner cannot be used to steer DESi."""

    def __init__(self, adapter: BenchmarkAdapter) -> None:
        self.adapter = adapter

    def run_one(self, task: BenchmarkTask) -> BenchmarkResult:
        return self.adapter.run(task)

    def run_all(
        self, tasks: Iterable[BenchmarkTask]
    ) -> tuple[BenchmarkResult, ...]:
        return tuple(self.adapter.run(task) for task in tasks)


def compare_results(
    a: BenchmarkResult, b: BenchmarkResult
) -> dict[str, object]:
    """Optional read-only COMPARISON layer (a peripheral DBA-style utility).

    Structurally compares two replay-bound results' core metrics. It is purely
    read-only: it asserts nothing about truth, introduces no ontology, and never
    folds or reconciles the underlying claims. Returns per-metric deltas plus a
    ``replay_equal`` flag — a benchmark convenience, never a governance
    decision."""
    ma, mb = a.metric_map(), b.metric_map()
    shared = sorted(set(ma) & set(mb))
    return {
        "task_id_a": a.task_id,
        "task_id_b": b.task_id,
        "replay_equal": a.replay_hash == b.replay_hash,
        "shared_metrics": shared,
        "only_in_a": sorted(set(ma) - set(mb)),
        "only_in_b": sorted(set(mb) - set(ma)),
        "metric_deltas": {k: mb[k] - ma[k] for k in shared},
        "both_traceable": a.is_traceable() and b.is_traceable(),
    }


__all__ = [
    "FORBIDDEN_BENCHMARK_OPERATIONS",
    "BenchmarkRunner",
    "ExtractorPort",
    "compare_results",
    "input_port",
    "is_forbidden",
    "output_port",
    "requested_forbidden",
]
