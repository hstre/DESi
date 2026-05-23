"""Aufgaben 6 + 9 — metrics, recommendation gate, replay hash."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_consistency_probe.report import (
    MIN_MANIPULATION_DETECTION,
    MIN_TENSION_RECALL,
    build_consistency_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_thresholds_are_strict() -> None:
    assert MIN_TENSION_RECALL >= 0.80
    assert MIN_MANIPULATION_DETECTION >= 0.80


def test_report_meets_corpus_minimum() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.corpus_total >= 60
    for n in r.corpus_per_group.values():
        assert n >= 20


def test_tension_recall_meets_threshold() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.metrics.tension_recall >= 0.80


def test_manipulation_rate_meets_threshold() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.manipulation_detection_rate >= 0.80


def test_contamination_is_zero() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.contamination.contamination_risk == 0.0


def test_recommendation_is_frame_tension_layer() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    # All three gates pass; the recommendation must be the
    # positive value, not NONE.
    assert r.recommended_next == "FRAME_TENSION_LAYER"


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_consistency_report(started_at=now, finished_at=now)
    b = build_consistency_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_consistency_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_consistency_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_to_dict_round_trips_json() -> None:
    import json
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0


def test_metrics_keys_complete() -> None:
    r = build_consistency_report(
        started_at=_now(), finished_at=_now(),
    )
    md = r.metrics.to_dict()
    for key in (
        "consistency_accuracy",
        "tension_recall",
        "conflict_precision",
        "undecidable_rate",
        "per_group_accuracy",
    ):
        assert key in md
