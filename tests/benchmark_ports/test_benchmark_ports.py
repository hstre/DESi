"""Benchmark-ports facade tests (PERIPHERAL).

Verifies the facade is benchmark periphery and nothing more: it builds
boundary-pinned tasks, refuses any core-mutating task, treats claims as
projections, runs replay-bound, and compares read-only. It never imports or
mutates a core epistemic module.
"""
from __future__ import annotations

from desi.benchmark_api import (
    SEARCH_COMPRESSION_BENCHMARK,
    BenchmarkAdapter,
    bind_result,
)
from desi.benchmark_api.constraints import covers_core_boundary
from desi.benchmark_ports import (
    FORBIDDEN_BENCHMARK_OPERATIONS,
    BenchmarkRunner,
    ExtractorPort,
    compare_results,
    input_port,
    output_port,
)

_SEARCH_METRICS = (
    "node_reduction", "branch_compression", "critical_branch_preservation",
    "novelty_preservation", "quality_preservation", "compute_reduction",
)


class _StubAdapter(BenchmarkAdapter):
    """Minimal peripheral adapter: maps a search-compression task into a
    replay-bound result. It reads task input only; it touches no core area."""

    benchmark_name = SEARCH_COMPRESSION_BENCHMARK

    def map(self, task):
        metrics = tuple((m, 1.0) for m in _SEARCH_METRICS)
        return bind_result(
            task,
            claim_outputs=(("branch", "kept"),),
            metrics=metrics,
            provenance=("test._StubAdapter",),
            limitations=("synthetic stub",),
        )


class _StubExtractor:
    name = "stub"

    def extract(self, payload):
        return (("claim", str(payload.get("q", ""))),)


def _task(task_id="t1", allowed=("adapter", "scorecard", "read_core_metric")):
    return input_port(
        task_id=task_id,
        benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
        payload={"q": "x"},
        allowed_operations=allowed,
    )


# --- input port pins the full protected-core boundary -----------------------
def test_input_port_pins_full_core_boundary() -> None:
    task = _task()
    assert task.forbidden_operations == FORBIDDEN_BENCHMARK_OPERATIONS
    assert covers_core_boundary(task.forbidden_operations)
    assert task.is_valid()


# --- a task that tries to steer the core is refused, not obeyed -------------
def test_runner_refuses_core_mutation() -> None:
    # placing a forbidden core-mutation op in the allowed list = steering attempt
    steered = _task(allowed=("adapter", "modify_governance_core"))
    result = BenchmarkRunner(_StubAdapter()).run_one(steered)
    assert result.is_refusal()
    assert result.claim_outputs == ()
    assert result.governance_status == "GOVERNANCE_INDEPENDENT"


# --- happy path: replay-bound, traceable, claims are projections ------------
def test_runner_produces_replay_bound_results() -> None:
    results = BenchmarkRunner(_StubAdapter()).run_all([_task("a"), _task("b")])
    assert len(results) == 2
    for r in results:
        assert r.is_replay_bound()
        assert r.is_traceable()
        assert not r.is_refusal()
        # claims appear only as projections (label, value) pairs
        assert all(isinstance(c, tuple) and len(c) == 2 for c in r.claim_outputs)


def test_output_port_is_serializable_record() -> None:
    r = BenchmarkRunner(_StubAdapter()).run_one(_task())
    rec = output_port(r)
    assert set(rec) == {
        "task_id", "claim_outputs", "metrics", "replay_hash",
        "provenance", "limitations", "refusal_reason_if_any",
        "governance_status",
    }


# --- comparison layer is read-only and replay-aware -------------------------
def test_compare_results_read_only() -> None:
    runner = BenchmarkRunner(_StubAdapter())
    r1 = runner.run_one(_task("same"))
    r2 = runner.run_one(_task("same"))
    cmp = compare_results(r1, r2)
    assert cmp["replay_equal"] is True
    assert cmp["both_traceable"] is True
    assert set(cmp["shared_metrics"]) == set(_SEARCH_METRICS)
    assert all(d == 0.0 for d in cmp["metric_deltas"].values())


# --- extractor port is a Protocol satisfied by a peripheral extractor -------
def test_extractor_port_protocol() -> None:
    ext = _StubExtractor()
    assert isinstance(ext, ExtractorPort)
    projections = ext.extract({"q": "hello"})
    assert projections == (("claim", "hello"),)
