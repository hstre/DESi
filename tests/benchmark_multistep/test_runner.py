"""Tests for v2.3 MultiStepBenchmarkRunner (Aufgabe 3)."""
from __future__ import annotations

from desi.benchmark_multistep import (
    ALL_MULTISTEP_CASES,
    MultiStepBenchmarkRunner,
    MultiStepResult,
)


def test_run_returns_one_result_per_case() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert len(run.results) == len(ALL_MULTISTEP_CASES)


def test_result_carries_required_fields() -> None:
    run = MultiStepBenchmarkRunner().run()
    for r in run.results:
        for f in (
            "case", "final_state", "depth_reached", "replay_hash",
            "cycle_detected", "blocked", "blocking_reason",
            "expected_depth_met", "expected_state_met",
            "expected_cycle_met", "expected_blocked_met",
        ):
            assert hasattr(r, f), f


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


def test_two_runs_produce_identical_final_states() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.final_state == rb.final_state


def test_two_runs_produce_identical_depth() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.depth_reached == rb.depth_reached


def test_runner_returns_run_with_timestamp() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert run.timestamp is not None


def test_runner_accepts_explicit_case_iterable() -> None:
    """A subset run should produce only that subset's results."""
    subset = ALL_MULTISTEP_CASES[:3]
    run = MultiStepBenchmarkRunner().run(subset)
    assert len(run.results) == 3
    assert [r.case.case_id for r in run.results] == [c.case_id for c in subset]


def test_no_result_has_negative_depth() -> None:
    run = MultiStepBenchmarkRunner().run()
    for r in run.results:
        assert r.depth_reached >= 0


def test_to_dict_round_trip() -> None:
    run = MultiStepBenchmarkRunner().run()
    d = run.to_dict()
    assert "results" in d
    assert len(d["results"]) == 30
