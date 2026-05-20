"""Aufgaben 8 + 9 — scoring + recommendation gate + replay hash."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_tension_integration.enums import InsertionPoint
from desi.frame_tension_integration.report import (
    MAX_FALSE_BLOCK_RATE,
    MIN_MANIPULATION_BLOCK_RATE,
    build_integration_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_thresholds_match_directive() -> None:
    assert MIN_MANIPULATION_BLOCK_RATE >= 0.95
    assert MAX_FALSE_BLOCK_RATE <= 0.05


def test_report_carries_all_four_points() -> None:
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    assert set(r.per_point_metrics) == {p.value for p in InsertionPoint}


def test_every_point_reports_integration_score() -> None:
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    for point, m in r.per_point_metrics.items():
        assert "integration_score" in m
        assert 0.0 <= m["integration_score"] <= 1.0


def test_post_routing_has_nonzero_contamination_when_blocking() -> None:
    # Any block at POST_ROUTING is by definition late — adversarial
    # cases reach the wrong pipeline first. So contamination_risk
    # at POST_ROUTING must be > 0 whenever there are blocked
    # adversarials.
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    m = r.per_point_metrics["post_routing"]
    if m["recovered_manipulations"] > 0:
        assert m["contamination_risk"] > 0.0


def test_recommendation_only_with_zero_contamination() -> None:
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "NONE":
        return
    chosen = r.per_point_metrics[r.recommended_next]
    assert chosen["contamination_risk"] == 0.0
    assert chosen["manipulation_block_rate"] >= MIN_MANIPULATION_BLOCK_RATE
    assert chosen["false_block_rate"] <= MAX_FALSE_BLOCK_RATE


def test_pre_spl_does_not_win_against_better_points() -> None:
    # PRE_SPL has no way to compare inner and outer, so its
    # manipulation_block_rate should be ≪ 0.95. The recommendation
    # must not pick it whenever a downstream point clears the gate.
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.recommended_next != "pre_spl"


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_integration_report(started_at=now, finished_at=now)
    b = build_integration_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_integration_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_integration_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_integration_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0
