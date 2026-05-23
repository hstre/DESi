"""Tests for BenchmarkRunner — shape + every required field per case."""
from __future__ import annotations

from desi.benchmark import (
    ALL_CASES,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunner,
)
from desi.recursive import ResolutionState


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------


def test_runner_returns_benchmark_run() -> None:
    run = BenchmarkRunner().run()
    assert isinstance(run, BenchmarkRun)


def test_runner_produces_one_result_per_case() -> None:
    run = BenchmarkRunner().run()
    assert len(run.results) == len(ALL_CASES) == 50


def test_each_result_carries_required_fields() -> None:
    run = BenchmarkRunner().run()
    required = (
        "case", "final_state", "bridge_count", "recursion_depth",
        "veto_count", "replay_hash", "false_positive", "false_negative",
    )
    for r in run.results:
        for f in required:
            assert hasattr(r, f), f"missing field {f} on {r.case.case_id}"


def test_each_result_has_a_resolution_state() -> None:
    run = BenchmarkRunner().run()
    for r in run.results:
        assert isinstance(r.final_state, ResolutionState)


def test_each_result_has_a_non_empty_replay_hash() -> None:
    run = BenchmarkRunner().run()
    for r in run.results:
        assert r.replay_hash.startswith("rr_")
        assert len(r.replay_hash) == 19


# ---------------------------------------------------------------------------
# Custom-case subset
# ---------------------------------------------------------------------------


def test_runner_accepts_a_custom_case_subset() -> None:
    from desi.benchmark import case_by_id
    subset = (case_by_id("B1"), case_by_id("B3"), case_by_id("C1"))
    run = BenchmarkRunner().run(subset)
    assert len(run.results) == 3
    ids = [r.case.case_id for r in run.results]
    assert ids == ["B1", "B3", "C1"]


# ---------------------------------------------------------------------------
# Per-case false-positive / false-negative flags are mutually consistent
# ---------------------------------------------------------------------------


def test_fp_and_fn_are_never_both_true() -> None:
    """A single case cannot be both a FP and a FN under the v1.5
    classifier."""
    run = BenchmarkRunner().run()
    for r in run.results:
        assert not (r.false_positive and r.false_negative), (
            f"{r.case.case_id} is both FP and FN"
        )


def test_runner_does_not_change_baseline_test_count() -> None:
    """Smoke check: BenchmarkRunner does not modify the resolver's
    behaviour on the existing test suites."""
    from desi.recursive import RecursiveResolver
    before = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    BenchmarkRunner().run()
    after = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert before.final_state == after.final_state
    assert before.replay_hash == after.replay_hash
