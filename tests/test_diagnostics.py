"""Tests for deterministic EN-event classification rules."""
from __future__ import annotations

from desi.diagnostics import (
    classify_en_event,
    compute_novelty_recovery,
    detect_penultimate_en_candidate,
)
from desi.models import ENEvent, Trajectory, TrajectoryStep


def _en(loop: int, novelty: float, **kw) -> ENEvent:
    base = dict(
        loop_index=loop,
        persona="historian",
        eni_novelty=novelty,
        eni_non_drift=0.5,
        eni_admissibility=0.5,
        admitted=True,
    )
    base.update(kw)
    return ENEvent(**base)


def test_eni_below_low_threshold_is_false_return():
    event = _en(loop=3, novelty=0.05)
    result = classify_en_event(event)
    assert result.label == "local_variation_or_false_return"


def test_eni_above_high_threshold_is_genuine_transformation():
    event = _en(loop=3, novelty=0.18)
    result = classify_en_event(event)
    assert result.label == "genuine_transformation"


def test_eni_in_band_is_borderline():
    for v in (0.10, 0.11, 0.12):
        event = _en(loop=1, novelty=v)
        assert classify_en_event(event).label == "borderline"


def test_novelty_recovery_detects_drop():
    event = _en(
        loop=2,
        novelty=0.20,
        novel_claims_next=4,
        dup_rate_before=0.42,
        dup_rate_after=0.18,
    )
    r = compute_novelty_recovery(event)
    assert r.recovered is True
    assert r.dup_delta is not None and r.dup_delta < 0


def test_novelty_recovery_requires_novel_claims_and_dup_drop():
    no_novel = _en(
        loop=2,
        novelty=0.20,
        novel_claims_next=0,
        dup_rate_before=0.42,
        dup_rate_after=0.18,
    )
    assert compute_novelty_recovery(no_novel).recovered is False

    no_drop = _en(
        loop=2,
        novelty=0.20,
        novel_claims_next=4,
        dup_rate_before=0.30,
        dup_rate_after=0.29,
    )
    assert compute_novelty_recovery(no_drop).recovered is False


def test_penultimate_en_candidate_when_principle_matches():
    traj = Trajectory(
        trajectory_id="t",
        steps=[TrajectoryStep(loop_index=0, operator="EXPOSITION")],
        en_events=[
            _en(loop=2, novelty=0.20),
            _en(loop=4, novelty=0.18),  # penultimate: genuine
            _en(loop=6, novelty=0.04),  # last: false return
        ],
    )
    p = detect_penultimate_en_candidate(traj)
    assert p.has_candidate is True
    assert p.penultimate_loop == 4
    assert p.last_loop == 6


def test_penultimate_en_not_applicable_with_one_event():
    traj = Trajectory(
        trajectory_id="t",
        steps=[TrajectoryStep(loop_index=0, operator="EXPOSITION")],
        en_events=[_en(loop=2, novelty=0.20)],
    )
    p = detect_penultimate_en_candidate(traj)
    assert p.has_candidate is False
