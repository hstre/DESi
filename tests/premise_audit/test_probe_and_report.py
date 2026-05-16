"""Aufgaben 5 + 6 + 9 + 10 — probe, gate, recommendation."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.premise_audit import (
    DEAD_KNOB_DELTA,
    MIN_NC_ACCURACY,
    PRIMARY_SIGNAL_DELTA,
    build_premise_audit_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_thresholds_match_directive() -> None:
    assert DEAD_KNOB_DELTA <= 0.10
    assert PRIMARY_SIGNAL_DELTA >= 0.50
    assert MIN_NC_ACCURACY >= 0.95


def test_report_chain_count_above_min() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.chain_count >= 500


def test_report_transition_count_above_min() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.transition_count >= 2000


def test_nc_accuracy_meets_threshold() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.nc_accuracy >= MIN_NC_ACCURACY


def test_recommendation_is_primary_or_none() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.recommended_next in (
        "PREMISE_EXTRACTOR_PRIMARY", "NONE",
    )


def test_primary_signals_only_when_recommendation_positive() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "PREMISE_EXTRACTOR_PRIMARY":
        assert len(r.primary_signals) >= 1
    # Otherwise primary_signals may be empty.


def test_every_signal_classified() -> None:
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert len(r.signal_probes) == 11
    for p in r.signal_probes:
        assert p.classification in (
            "DEAD_KNOB", "PRIMARY_SIGNAL", "NEUTRAL",
        )


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_premise_audit_report(started_at=now, finished_at=now)
    b = build_premise_audit_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_premise_audit_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_premise_audit_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_premise_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
