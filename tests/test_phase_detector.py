"""Tests for the DESi 5-phase model."""
from __future__ import annotations

from desi.models import ENEvent, Trajectory, TrajectoryStep
from desi.phase_detector import (
    PHASE_I,
    PHASE_II,
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


def test_phase_ii_span_is_well_ordered():
    """DET-FAL T10 regression: Phase II must satisfy start_loop <= end_loop.

    When the first novelty collapse occurs at a loop *after* the first EN
    event, the legacy detector emitted start_loop=collapse_loop and
    end_loop=first_en.loop_index, producing a malformed span like
    `loops 3..2`. This test reproduces that exact shape (collapse at loop 3,
    EN at loop 2) and asserts the span is well-ordered.
    """
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=6, dup=0.20, op="T3"),
            _step(1, novel=3, dup=0.55, op="T8"),
            _step(2, novel=8, dup=0.30, op="T5"),
            _step(3, novel=1, dup=0.45, op="T6"),  # first collapse at loop 3
        ],
        en_events=[
            _en(loop=2, novelty=0.13),  # first EN at loop 2 — BEFORE the collapse
        ],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_II in spans, "expected Phase II to trigger on this shape"
    span = spans[PHASE_II]
    assert span.start_loop <= span.end_loop, (
        f"Phase II span is malformed: loops {span.start_loop}..{span.end_loop}"
    )


def test_phase_v_closes_on_reversal():
    """DET-FAL T9 regression: Phase V must close when its trigger condition
    stops holding for >=2 consecutive subsequent loops.

    Shape: dup crosses 0.50 with novel<=1 at loop 2, holds through loop 4,
    then trajectory recovers (dup drops, novel rises) at loops 5-7. The
    legacy detector reported Phase V loops 2..7 (sticky). Post-cycle-2 it
    should close at loop 4 (last loop where the trigger held).
    """
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=3, dup=0.30),
            _step(2, novel=1, dup=0.55),  # Phase V triggers here
            _step(3, novel=0, dup=0.65),  # still holds
            _step(4, novel=0, dup=0.75),  # still holds (last_held)
            _step(5, novel=8, dup=0.20),  # broken
            _step(6, novel=6, dup=0.25),  # broken (>=2 consecutive -> close)
            _step(7, novel=4, dup=0.30),
        ],
        en_events=[],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].start_loop == 2
    assert spans[PHASE_V].end_loop == 4, (
        f"Phase V should close at last_held=4, got {spans[PHASE_V].end_loop}"
    )
