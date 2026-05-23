"""Aufgaben 2 + 4 + 6 + report — separability, NC, gates."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.epistemic_trajectory import (
    DEAD_KNOB_DELTA,
    FRAME_TENSION_PRIMARY_THRESHOLD,
    MIN_NC_ACCURACY,
    MIN_SEPARABILITY,
    MIN_TRAJECTORY_COUNT,
    MIN_TRANSITION_COUNT,
    build_trajectory_report,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_trajectory_count_above_min() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.trajectory_count >= MIN_TRAJECTORY_COUNT


def test_transition_count_above_min() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.transition_count >= MIN_TRANSITION_COUNT


def test_negative_control_accuracy_meets_threshold() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.nc_accuracy >= MIN_NC_ACCURACY


def test_contamination_is_zero() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.contamination_count == 0


def test_dead_knob_flag_triggers_deprecation_recommendation() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.dead_knob_candidate is not None:
        assert r.recommended_next == (
            "CAUSAL_CHAIN_DEPRECATION_PROBE"
        )


def test_separability_delta_consistent_with_dead_knob_flag() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.separability_delta < DEAD_KNOB_DELTA:
        assert r.dead_knob_candidate == "CAUSAL_CHAIN"
    else:
        assert r.dead_knob_candidate is None


def test_thresholds_match_directive() -> None:
    assert MIN_TRAJECTORY_COUNT >= 400
    assert MIN_TRANSITION_COUNT >= 1500
    assert MIN_NC_ACCURACY >= 0.95
    assert MIN_SEPARABILITY >= 0.80
    assert DEAD_KNOB_DELTA <= 0.10
    assert FRAME_TENSION_PRIMARY_THRESHOLD >= 0.50


def test_per_source_counts_cover_all_sources() -> None:
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    for src in (
        "sample_trajectories", "v23_multistep", "v314_heldout",
        "v315_adversarial", "v316_surviving",
        "v318_weird_marker_free",
    ):
        assert src in r.per_source_counts


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_trajectory_report(started_at=now, finished_at=now)
    b = build_trajectory_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_trajectory_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_trajectory_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_trajectory_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
