"""Tests for v2.3 hard-constraint checker (Aufgabe 5)."""
from __future__ import annotations

from desi.benchmark_multistep import (
    MultiStepBenchmarkRunner,
    check_hard_constraints,
)


def test_two_runs_yield_no_replay_drift() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    report = check_hard_constraints(a, b)
    assert report.replay_drift is False


def test_constraint_report_carries_required_fields() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    report = check_hard_constraints(a, b)
    for f in (
        "passed", "replay_drift", "authority_breach_ids",
        "cycle_breach_ids", "insufficient_depth_ids", "reasons",
    ):
        assert hasattr(report, f)


def test_constraint_report_is_deterministic() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    rep1 = check_hard_constraints(a, b)
    a2 = MultiStepBenchmarkRunner().run()
    b2 = MultiStepBenchmarkRunner().run()
    rep2 = check_hard_constraints(a2, b2)
    assert rep1.replay_drift == rep2.replay_drift
    assert rep1.authority_breach_ids == rep2.authority_breach_ids
    assert rep1.cycle_breach_ids == rep2.cycle_breach_ids
    assert rep1.insufficient_depth_ids == rep2.insufficient_depth_ids


def test_to_dict_shape() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    rep = check_hard_constraints(a, b)
    d = rep.to_dict()
    for k in (
        "passed", "replay_drift", "authority_breach_ids",
        "cycle_breach_ids", "insufficient_depth_ids", "reasons",
    ):
        assert k in d


def test_passed_implies_all_constraint_sets_empty() -> None:
    """Logical contract — even if today's run violates constraints,
    the implication holds."""
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    rep = check_hard_constraints(a, b)
    if rep.passed:
        assert rep.replay_drift is False
        assert rep.authority_breach_ids == ()
        assert rep.cycle_breach_ids == ()
        assert rep.insufficient_depth_ids == ()


def test_replay_drift_detected_when_hashes_diverge() -> None:
    """Synthesise a fake drift by mutating one result's replay_hash."""
    from dataclasses import replace
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    # Tamper with the first result of run_b
    tampered_first = replace(b.results[0], replay_hash="ZZZZ")
    tampered_b = b.__class__(
        timestamp=b.timestamp,
        results=(tampered_first,) + b.results[1:],
    )
    rep = check_hard_constraints(a, tampered_b)
    assert rep.replay_drift is True
    assert rep.passed is False
