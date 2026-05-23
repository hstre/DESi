"""Aufgaben 8 + 9 — report aggregation, recommendation gate, replay hash."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_context_probe.report import (
    MAX_FALSE_INHERITANCE_RATE,
    MIN_INHERITANCE_ACCURACY,
    build_context_probe_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_report_passes_target_minimum() -> None:
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    assert rep.target_count >= 25


def test_report_runs_ten_false_inheritance_fixtures() -> None:
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    assert rep.false_inheritance_count >= 10


def test_report_recommendation_is_none_due_to_false_inheritance() -> None:
    # The naïve inheritance simulator absorbs every misleading
    # window — absorption_rate = 1.0 — so the gate must collapse
    # to NONE and the reason must mention the false-inheritance
    # absorption rate.
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    assert rep.recommended_next == "NONE"
    assert "false_inheritance_absorption_rate" in rep.recommendation_reason


def test_recommendation_reason_mentions_contamination() -> None:
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    # ``Frame: …`` explicit markers and domain-token phrases overlap
    # protected pools, so the contamination clause must show up too.
    assert "contamination" in rep.recommendation_reason


def test_inheritance_summary_consistent() -> None:
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    s = rep.inheritance_summary
    assert s.total == rep.target_count
    assert 0.0 <= s.accuracy <= 1.0
    assert sum(s.by_signal.values()) == s.total
    assert sum(s.by_layer.values()) == s.total


def test_false_inheritance_summary_consistent() -> None:
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    s = rep.false_inheritance_summary
    assert s.total == rep.false_inheritance_count
    assert s.absorbed_misleading == s.total
    assert s.correct_against_ground_truth == 0
    assert s.absorption_rate == 1.0


def test_thresholds_are_strict() -> None:
    # If anyone loosens the gate, this test catches it.
    assert MIN_INHERITANCE_ACCURACY >= 0.95
    assert MAX_FALSE_INHERITANCE_RATE <= 0.10


def test_replay_hash_is_deterministic() -> None:
    now = _now()
    a = build_context_probe_report(started_at=now, finished_at=now)
    b = build_context_probe_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_context_probe_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_context_probe_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_to_dict_round_trip_serialisable() -> None:
    import json
    rep = build_context_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    payload = rep.to_dict()
    # Survives canonical JSON encoding — no surprise dataclass leaks.
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert isinstance(blob, str) and len(blob) > 0
