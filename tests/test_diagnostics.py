"""Tests for deterministic EN-event classification rules."""
from __future__ import annotations

from desi.diagnostics import (
    classify_en_event,
    compute_novelty_recovery,
    detect_penultimate_en_candidate,
)
from desi.models import ENEvent, Trajectory, TrajectoryStep


def _en(loop: int, novelty: float, **kw) -> ENEvent:
    base = dict(loop_index=loop, persona="historian", eni_novelty=novelty,
                eni_non_drift=0.5, eni_admissibility=0.5, admitted=True)
    base.update(kw)
    return ENEvent(**base)


def test_eni_below_low_threshold_is_false_return():
    assert classify_en_event(_en(3, 0.05)).label == "local_variation_or_false_return"


def test_eni_above_high_threshold_is_genuine_transformation():
    assert classify_en_event(_en(3, 0.18)).label == "genuine_transformation"


def test_eni_in_band_is_borderline():
    for v in (0.10, 0.11, 0.12):
        assert classify_en_event(_en(1, v)).label == "borderline"


def test_novelty_recovery_detects_drop():
    r = compute_novelty_recovery(_en(2, 0.20, novel_claims_next=4, dup_rate_before=0.42, dup_rate_after=0.18))
    assert r.recovered is True
    assert r.dup_delta is not None and r.dup_delta < 0


def test_novelty_recovery_requires_novel_claims_and_dup_drop():
    assert compute_novelty_recovery(_en(2, 0.20, novel_claims_next=0, dup_rate_before=0.42, dup_rate_after=0.18)).recovered is False
    assert compute_novelty_recovery(_en(2, 0.20, novel_claims_next=4, dup_rate_before=0.30, dup_rate_after=0.29)).recovered is False


def test_penultimate_en_candidate_when_principle_matches():
    traj = Trajectory(
        trajectory_id="t",
        steps=[TrajectoryStep(loop_index=0, operator="EXPOSITION")],
        en_events=[
            _en(2, 0.20),
            _en(4, 0.18, novel_claims_next=4, dup_rate_before=0.45, dup_rate_after=0.20),
            _en(6, 0.04),
        ],
    )
    p = detect_penultimate_en_candidate(traj)
    assert p.has_candidate is True
    assert p.penultimate_loop == 4
    assert p.last_loop == 6


def test_penultimate_en_unconfirmed_does_not_count():
    traj = Trajectory(
        trajectory_id="t",
        steps=[TrajectoryStep(loop_index=0, operator="EXPOSITION")],
        en_events=[
            _en(2, 0.20),
            _en(4, 0.15, novel_claims_next=0, dup_rate_before=0.45, dup_rate_after=0.55),
            _en(6, 0.04),
        ],
    )
    p = detect_penultimate_en_candidate(traj)
    assert p.has_candidate is False
    assert p.penultimate_label != "genuine_transformation_confirmed"


def test_penultimate_en_not_applicable_with_one_event():
    traj = Trajectory(
        trajectory_id="t",
        steps=[TrajectoryStep(loop_index=0, operator="EXPOSITION")],
        en_events=[_en(2, 0.20)],
    )
    assert detect_penultimate_en_candidate(traj).has_candidate is False


def test_detect_branch_explosion_fires_on_adv07_shape():
    from desi.diagnostics import detect_branch_explosion
    from desi.models import ClaimState
    steps = []
    for i in range(6):
        claims = [ClaimState(id=f"B{i:03d}{j}", branch_open=True, parent_id=f"C00{i}") for j in range(2)]
        steps.append(TrajectoryStep(loop_index=i, focus_claim_id=f"C00{i}", operator="T1", novel_claims=8, dup_rate=0.10, claims=claims))
    traj = Trajectory(trajectory_id="branch_explosion_shape", steps=steps, en_events=[], terminal_failure_mode="GRAPH_TOO_LARGE")
    assert detect_branch_explosion(traj).detected is True


def test_detect_branch_explosion_does_not_fire_on_attractor_lock():
    from desi.diagnostics import detect_branch_explosion
    from desi.models import ClaimState
    steps = [
        TrajectoryStep(loop_index=i, focus_claim_id="C001", operator="T8",
                       novel_claims=max(0, 12 - 2*i), dup_rate=min(0.85, 0.05 + 0.15*i),
                       claims=[ClaimState(id="C001", branch_open=False)])
        for i in range(6)
    ]
    traj = Trajectory(trajectory_id="attractor_lock_shape", steps=steps, en_events=[], terminal_failure_mode="ATTRACTOR_LOCK")
    assert detect_branch_explosion(traj).detected is False


def test_detect_mild_stagnation_fires_on_adv04_shape():
    from desi.diagnostics import detect_mild_stagnation
    traj = Trajectory(
        trajectory_id="adv04_shape",
        steps=[
            TrajectoryStep(loop_index=0, operator="T3", novel_claims=9, dup_rate=0.15),
            TrajectoryStep(loop_index=1, operator="T4", novel_claims=3, dup_rate=0.30),
            TrajectoryStep(loop_index=2, operator="T6", novel_claims=2, dup_rate=0.35),
            TrajectoryStep(loop_index=3, operator="T7", novel_claims=2, dup_rate=0.38),
            TrajectoryStep(loop_index=4, operator="T8", novel_claims=2, dup_rate=0.40),
            TrajectoryStep(loop_index=5, operator="T8", novel_claims=2, dup_rate=0.42),
            TrajectoryStep(loop_index=6, operator="T8", novel_claims=2, dup_rate=0.45),
        ],
        en_events=[],
    )
    assert detect_mild_stagnation(traj).detected is True


def test_detect_mild_stagnation_suppressed_by_phase_v_trigger():
    from desi.diagnostics import detect_mild_stagnation
    traj = Trajectory(
        trajectory_id="phase_v_shape",
        steps=[
            TrajectoryStep(loop_index=0, operator="T3", novel_claims=10, dup_rate=0.05),
            TrajectoryStep(loop_index=1, operator="T8", novel_claims=1, dup_rate=0.55),
            TrajectoryStep(loop_index=2, operator="T8", novel_claims=0, dup_rate=0.65),
            TrajectoryStep(loop_index=3, operator="T8", novel_claims=0, dup_rate=0.75),
        ],
        en_events=[],
    )
    assert detect_mild_stagnation(traj).detected is False


def test_validate_step_metric_coherence_flags_contradictory_step():
    from desi.diagnostics import validate_step_metric_coherence
    traj = Trajectory(
        trajectory_id="incoherent",
        steps=[
            TrajectoryStep(loop_index=0, operator="T3", novel_claims=10, dup_rate=0.05),
            TrajectoryStep(loop_index=1, operator="T8", novel_claims=10, dup_rate=0.90),
        ],
        en_events=[],
    )
    assert validate_step_metric_coherence(traj).detected is True


def test_validate_step_metric_coherence_clean_trajectory():
    from desi.diagnostics import validate_step_metric_coherence
    traj = Trajectory(
        trajectory_id="clean",
        steps=[
            TrajectoryStep(loop_index=0, operator="T3", novel_claims=10, dup_rate=0.10),
            TrajectoryStep(loop_index=1, operator="T4", novel_claims=4, dup_rate=0.30),
            TrajectoryStep(loop_index=2, operator="T8", novel_claims=1, dup_rate=0.55),
        ],
        en_events=[],
    )
    assert validate_step_metric_coherence(traj).detected is False


def test_composite_en_high_eni_without_recovery_is_unconfirmed():
    from desi.diagnostics import classify_en_event_composite
    r = classify_en_event_composite(_en(1, 0.25, novel_claims_next=0, dup_rate_before=0.40, dup_rate_after=0.50))
    assert r.label == "genuine_transformation_unconfirmed"


def test_composite_en_borderline_with_recovery_is_distinguished():
    from desi.diagnostics import classify_en_event_composite
    r = classify_en_event_composite(_en(2, 0.11, novel_claims_next=5, dup_rate_before=0.50, dup_rate_after=0.20))
    assert r.label == "borderline_with_recovery"


def test_composite_en_high_with_recovery_is_confirmed():
    from desi.diagnostics import classify_en_event_composite
    r = classify_en_event_composite(_en(2, 0.18, novel_claims_next=4, dup_rate_before=0.42, dup_rate_after=0.18))
    assert r.label == "genuine_transformation_confirmed"


# Generalization-loop cycle 1: attractor detector's tail-saturation guard.
def test_detect_terminal_attractor_skips_unsaturated_tail():
    from desi.diagnostics import detect_terminal_attractor_subjects
    traj = Trajectory(
        trajectory_id="unsaturated_tail",
        steps=[
            TrajectoryStep(loop_index=i, focus_claim_id="C001",
                           operator="T3", novel_claims=5, dup_rate=0.20)
            for i in range(5)
        ],
        en_events=[],
    )
    r = detect_terminal_attractor_subjects(traj)
    assert r.candidate_claim_ids == []
    assert "tail not saturated" in r.note


def test_detect_terminal_attractor_fires_on_saturated_tail():
    from desi.diagnostics import detect_terminal_attractor_subjects
    traj = Trajectory(
        trajectory_id="saturated_tail",
        steps=[
            TrajectoryStep(loop_index=i, focus_claim_id="C001",
                           operator="T8", novel_claims=1, dup_rate=0.60)
            for i in range(5)
        ],
        en_events=[],
    )
    r = detect_terminal_attractor_subjects(traj)
    assert r.candidate_claim_ids == ["C001"]
    assert "tail saturated" in r.note


# Generalization-loop cycle 3: branch_explosion averages over tail-3, not whole trajectory.
def test_branch_explosion_does_not_fire_on_late_synthesis_recovery():
    from desi.diagnostics import detect_branch_explosion
    from desi.models import ClaimState
    steps = []
    for i in range(5):
        claims = [ClaimState(id=f"B{i}{j}", branch_open=True, parent_id=f"P{i}") for j in range(2)]
        steps.append(TrajectoryStep(loop_index=i, focus_claim_id="C001",
                                    operator="T1", novel_claims=7, dup_rate=0.12,
                                    claims=claims))
    for i in range(5, 8):
        steps.append(TrajectoryStep(loop_index=i, focus_claim_id="C001",
                                    operator="T9", novel_claims=3, dup_rate=0.30,
                                    claims=[ClaimState(id="S001", branch_open=False)]))
    traj = Trajectory(trajectory_id="branch_then_synthesis", steps=steps, en_events=[])
    r = detect_branch_explosion(traj)
    assert r.detected is False, f"expected late-synthesis to suppress; got {r.note}"


# Generalization-loop cycle 5: borderline-chain detector.
def test_detect_borderline_chain_fires_on_four_borderlines():
    from desi.diagnostics import detect_borderline_chain
    traj = Trajectory(
        trajectory_id="gen11_shape",
        steps=[TrajectoryStep(loop_index=i, operator="T3", novel_claims=5, dup_rate=0.20)
               for i in range(8)],
        en_events=[
            _en(1, 0.11), _en(3, 0.10), _en(5, 0.12), _en(7, 0.11),
        ],
    )
    r = detect_borderline_chain(traj)
    assert r.detected is True
    assert r.longest_run == 4


def test_detect_borderline_chain_does_not_fire_on_mixed_labels():
    from desi.diagnostics import detect_borderline_chain
    traj = Trajectory(
        trajectory_id="mixed",
        steps=[TrajectoryStep(loop_index=i, operator="T3", novel_claims=5, dup_rate=0.20)
               for i in range(6)],
        en_events=[
            _en(1, 0.11), _en(3, 0.20), _en(5, 0.11),
        ],
    )
    r = detect_borderline_chain(traj)
    assert r.detected is False
