"""Tests for the DESi 5-phase model."""
from __future__ import annotations

from desi.models import ENEvent, Trajectory, TrajectoryStep
from desi.phase_detector import (
    PHASE_I,
    PHASE_IV,
    PHASE_V,
    detect_phases,
)


def _step(loop: int, *, novel: int = 0, dup: float = 0.0, op: str = "T3",
          failure: str | None = None) -> TrajectoryStep:
    return TrajectoryStep(
        loop_index=loop,
        focus_claim_id=f"c{loop}",
        operator=op,
        novel_claims=novel,
        dup_rate=dup,
        failure_mode=failure,
        claims=[],
    )


def _en(loop: int, novelty: float) -> ENEvent:
    return ENEvent(
        loop_index=loop,
        persona="historian",
        eni_novelty=novelty,
        eni_non_drift=0.5,
        eni_admissibility=0.5,
        admitted=True,
    )


def test_phase_i_triggers_on_exposition_with_high_novelty_and_low_dup():
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=12, dup=0.05, op="T3")],
        en_events=[],
    )
    names = [p.name for p in detect_phases(traj).phases]
    assert PHASE_I in names


def test_two_consecutive_low_eni_events_trigger_phase_iv():
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=2, dup=0.30),
            _step(2, novel=1, dup=0.55),
            _step(3, novel=0, dup=0.65),
        ],
        en_events=[
            _en(2, 0.05),
            _en(3, 0.07),
        ],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_IV in spans
    assert spans[PHASE_IV].start_loop == 2
    assert spans[PHASE_IV].end_loop == 3


def test_non_consecutive_low_eni_does_not_trigger_phase_iv():
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=2, dup=0.30),
            _step(2, novel=3, dup=0.30),
            _step(3, novel=0, dup=0.60),
        ],
        en_events=[
            _en(2, 0.05),
            _en(3, 0.20),  # genuine -> resets the run
        ],
    )
    names = [p.name for p in detect_phases(traj).phases]
    assert PHASE_IV not in names


def test_phase_v_triggers_on_dup_high_and_novel_low():
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=1, dup=0.55, op="T8"),
        ],
        en_events=[],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].start_loop == 1
    assert spans[PHASE_V].confidence == "high"


def test_phase_v_does_not_trigger_below_threshold():
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=3, dup=0.40),
            _step(2, novel=2, dup=0.45),
        ],
        en_events=[],
    )
    names = [p.name for p in detect_phases(traj).phases]
    assert PHASE_V not in names


def test_terminal_failure_alone_triggers_phase_v_with_medium_confidence():
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=4, dup=0.30),
        ],
        en_events=[],
        terminal_failure_mode="PREMATURE_TERMINATION",
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].confidence == "medium"
