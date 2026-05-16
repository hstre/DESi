"""v3.23 — simulator + report + safety/efficiency classification."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.gate_latency import (
    EfficiencyClass,
    MIN_NC_ACCURACY,
    StackName,
    all_chains,
    all_stacks,
    build_gate_latency_report,
    classify_delta,
    run_negative_controls,
    transitions_per_chain,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_three_stacks() -> None:
    assert len(list(StackName)) == 3
    assert len(all_stacks()) == 3


def test_corpus_meets_minimums() -> None:
    chains = all_chains()
    attacks = sum(1 for c in chains if c.is_attack)
    assert len(chains) >= 600
    assert attacks >= 400
    assert len(chains) * transitions_per_chain() >= 3000


def test_nc_accuracy_meets_threshold() -> None:
    _outs, acc, _shape = run_negative_controls()
    assert acc >= MIN_NC_ACCURACY


def test_classify_delta_thresholds() -> None:
    assert classify_delta(0.0) is EfficiencyClass.NO_GAIN
    assert classify_delta(0.01) is EfficiencyClass.NO_GAIN
    assert classify_delta(0.15) is EfficiencyClass.NO_GAIN
    assert classify_delta(0.20) is EfficiencyClass.SIGNIFICANT_GAIN
    assert classify_delta(0.25) is EfficiencyClass.SIGNIFICANT_GAIN
    assert classify_delta(0.30) is EfficiencyClass.MAJOR_GAIN
    assert classify_delta(0.5) is EfficiencyClass.MAJOR_GAIN


def test_report_emits_three_stacks() -> None:
    r = build_gate_latency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert len(r.evaluations) == 3


def test_baseline_metric_present() -> None:
    r = build_gate_latency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.baseline.stack == StackName.S1_CURRENT_ORDER.value


def test_recommendation_in_allowed_set() -> None:
    r = build_gate_latency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.recommended_next in {
        "LATENCY_OPTIMIZED_STACK",
        "KEEP_CURRENT_STACK",
        "NONE",
    }


def test_optimized_stack_only_when_significant_gain_and_safe() -> None:
    r = build_gate_latency_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "LATENCY_OPTIMIZED_STACK":
        assert r.best_stack is not None
        chosen = next(
            e for e in r.evaluations
            if e.metrics.stack == r.best_stack
        )
        assert chosen.is_safety_valid
        assert chosen.efficiency in (
            "SIGNIFICANT_GAIN", "MAJOR_GAIN",
        )


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_gate_latency_report(started_at=now, finished_at=now)
    b = build_gate_latency_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_gate_latency_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_gate_latency_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_gate_latency_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
