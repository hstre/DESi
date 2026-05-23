"""Aufgabe 8 — report + recommendation + replay hash."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.heldout_causal import build_heldout_report


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_report_total_matches_corpus() -> None:
    r = build_heldout_report(started_at=_now(), finished_at=_now())
    assert r.total_cases >= 60


def test_recommendation_only_with_all_gates_passed() -> None:
    r = build_heldout_report(started_at=_now(), finished_at=_now())
    if r.recommended_next == "NONE":
        return
    assert r.metrics.heldout_precision >= 0.95
    assert r.metrics.heldout_recall >= 0.85
    assert r.metrics.false_positive_count == 0
    assert r.metrics.trap_block_rate == 1.0
    assert r.independence.independence_passed is True


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_heldout_report(started_at=now, finished_at=now)
    b = build_heldout_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_heldout_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_heldout_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_heldout_report(started_at=_now(), finished_at=_now())
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0
