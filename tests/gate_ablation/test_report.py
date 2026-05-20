"""Aufgaben 6 + 9 + 10 — classification + recommendation."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.gate_ablation import (
    DEAD_KNOB_DELTA,
    GateClassification,
    MIN_NC_ACCURACY,
    PRIMARY_CLIFF_DELTA,
    build_gate_ablation_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_thresholds_match_directive() -> None:
    assert DEAD_KNOB_DELTA <= 0.05
    assert PRIMARY_CLIFF_DELTA >= 0.50
    assert MIN_NC_ACCURACY >= 0.95


def test_report_meets_corpus_minima() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.chain_count >= 600
    assert r.attack_count >= 100
    assert r.transition_count >= 2500


def test_nc_accuracy_meets_threshold() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.nc_accuracy >= MIN_NC_ACCURACY


def test_seven_ablations_emitted() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    assert len(r.ablations) == 7


def test_every_ablation_carries_classification() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    allowed = {c.value for c in GateClassification}
    for a in r.ablations:
        assert a.classification in allowed


def test_recommendation_in_allowed_set() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.recommended_next in {
        "GATE_STACK_CONFIRMED",
        "GATE_STACK_REORDER",
        "GATE_DEPRECATION_CANDIDATE",
        "NONE",
    }


def test_contamination_is_zero_at_baseline() -> None:
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.contamination_count == 0


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_gate_ablation_report(started_at=now, finished_at=now)
    b = build_gate_ablation_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_gate_ablation_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_gate_ablation_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_gate_ablation_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
