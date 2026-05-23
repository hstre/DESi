"""Aufgaben 3 + 8 — metrics + recommendation gate + replay hash."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_tension_audit.report import (
    MIN_TENSION_PRECISION_FOR_PATCH,
    build_tension_audit_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_metrics_keys_complete() -> None:
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    md = r.metrics.to_dict()
    for key in (
        "total_tension_cases",
        "true_tension_count",
        "false_tension_count",
        "ambiguous_tension_count",
        "tension_precision",
        "false_tension_rate",
        "ambiguous_tension_rate",
    ):
        assert key in md


def test_total_tension_cases_positive() -> None:
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.metrics.total_tension_cases > 0


def test_true_plus_false_plus_ambiguous_equals_total() -> None:
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    m = r.metrics
    assert (
        m.true_tension_count
        + m.false_tension_count
        + m.ambiguous_tension_count
    ) == m.total_tension_cases


def test_precision_threshold_value() -> None:
    assert MIN_TENSION_PRECISION_FOR_PATCH >= 0.90


def test_recommendation_is_none_without_patchable_cluster() -> None:
    # With the current v3.9 artifact the only FALSE/AMBIGUOUS
    # cluster is size 1, so no cluster reaches MIN_PATCHABLE_SIZE
    # and the recommendation must be NONE. If a future artifact
    # surfaces a patchable cluster, this test should be updated
    # alongside the directive's expectation.
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    if all(not p.patchable for p in r.patchability):
        assert r.recommended_next == "NONE"


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_tension_audit_report(started_at=now, finished_at=now)
    b = build_tension_audit_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_tension_audit_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_tension_audit_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0


def test_no_recommendation_without_zero_contamination() -> None:
    # If recommended_next is anything other than NONE, the chosen
    # cluster's patchability verdict must have both contamination
    # metrics at zero. This is the directive's hard guarantee.
    r = build_tension_audit_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "NONE":
        return
    chosen = next(
        p for p in r.patchability if p.cluster_id == r.recommended_next
    )
    assert chosen.contamination_risk == 0.0
    assert chosen.manipulation_absorption_risk == 0.0
    assert chosen.patchable is True
