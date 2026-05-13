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
            _en(loop=4, novelty=0.18),
            _en(loop=6, novelty=0.04),
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


def test_detect_branch_explosion_fires_on_adv07_shape():
    """DET-FAL T7 regression: many open branches + low dup + high novel must
    trigger branch_explosion.detected=True. Calibrated to adv07."""
    from desi.diagnostics import detect_branch_explosion
    from desi.models import ClaimState
    steps = []
    for i in range(6):
        claims = [
            ClaimState(id=f"B{i:03d}{j}", branch_open=True, parent_id=f"C00{i}")
            for j in range(2)
        ]
        steps.append(TrajectoryStep(
            loop_index=i, focus_claim_id=f"C00{i}", operator="T1",
            novel_claims=8, dup_rate=0.10, claims=claims,
        ))
    traj = Trajectory(
        trajectory_id="branch_explosion_shape",
        steps=steps, en_events=[],
        terminal_failure_mode="GRAPH_TOO_LARGE",
    )
    report = detect_branch_explosion(traj)
    assert report.detected is True
    assert report.distinct_open_branches >= 5
    assert report.avg_dup_rate < 0.20
    assert report.avg_novel_claims >= 5


def test_detect_branch_explosion_does_not_fire_on_attractor_lock():
    """Negative regression: an attractor-lock trajectory (no open branches,
    rising dup, falling novel) must not trigger branch_explosion."""
    from desi.diagnostics import detect_branch_explosion
    from desi.models import ClaimState
    steps = [
        TrajectoryStep(
            loop_index=i, focus_claim_id="C001", operator="T8",
            novel_claims=max(0, 12 - 2*i), dup_rate=min(0.85, 0.05 + 0.15*i),
            claims=[ClaimState(id="C001", branch_open=False)],
        )
        for i in range(6)
    ]
    traj = Trajectory(
        trajectory_id="attractor_lock_shape",
        steps=steps, en_events=[], terminal_failure_mode="ATTRACTOR_LOCK",
    )
    assert detect_branch_explosion(traj).detected is False
