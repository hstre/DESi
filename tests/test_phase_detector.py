"""Tests for the DESi 5-phase model."""
from __future__ import annotations

from desi.models import ENEvent, Trajectory, TrajectoryStep
from desi.phase_detector import (
    PHASE_I, PHASE_II, PHASE_IV, PHASE_V, detect_phases,
)


def _step(loop: int, *, novel: int = 0, dup: float = 0.0, op: str = "T3",
          failure: str | None = None) -> TrajectoryStep:
    return TrajectoryStep(
        loop_index=loop, focus_claim_id=f"c{loop}", operator=op,
        novel_claims=novel, dup_rate=dup, failure_mode=failure, claims=[],
    )


def _en(loop: int, novelty: float) -> ENEvent:
    return ENEvent(
        loop_index=loop, persona="historian", eni_novelty=novelty,
        eni_non_drift=0.5, eni_admissibility=0.5, admitted=True,
    )


def test_phase_i_triggers_on_exposition_with_high_novelty_and_low_dup():
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=12, dup=0.05, op="T3")],
        en_events=[],
    )
    assert PHASE_I in [p.name for p in detect_phases(traj).phases]


def test_two_consecutive_low_eni_events_trigger_phase_iv():
    # Generalization-loop cycle 2: avoid co-firing Phase V on the same loops
    # so the assertion about Phase IV's span is independent of Phase V's
    # post-clip subsumption. Dup is kept below the Phase V trigger.
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=2, dup=0.30),
            _step(2, novel=1, dup=0.40),
            _step(3, novel=0, dup=0.45),
        ],
        en_events=[_en(2, 0.05), _en(3, 0.07)],
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
        en_events=[_en(2, 0.05), _en(3, 0.20)],
    )
    assert PHASE_IV not in [p.name for p in detect_phases(traj).phases]


def test_phase_v_triggers_on_dup_high_and_novel_low():
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=11, dup=0.05, op="T3"),
               _step(1, novel=1, dup=0.55, op="T8")],
        en_events=[],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].start_loop == 1


def test_phase_v_does_not_trigger_below_threshold():
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=11, dup=0.05, op="T3"),
               _step(1, novel=3, dup=0.40),
               _step(2, novel=2, dup=0.45)],
        en_events=[],
    )
    assert PHASE_V not in [p.name for p in detect_phases(traj).phases]


def test_terminal_failure_alone_triggers_phase_v_with_medium_confidence():
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=11, dup=0.05, op="T3"),
               _step(1, novel=4, dup=0.30)],
        en_events=[],
        terminal_failure_mode="PREMATURE_TERMINATION",
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].confidence == "medium"


def test_phase_ii_span_is_well_ordered():
    """DET-FAL T10. Post-cycle-9: trajectory extended for persistence rule."""
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=6, dup=0.20, op="T3"),
            _step(1, novel=3, dup=0.55, op="T8"),
            _step(2, novel=8, dup=0.30, op="T5"),
            _step(3, novel=1, dup=0.45, op="T6"),
            _step(4, novel=1, dup=0.50, op="T8"),
        ],
        en_events=[_en(loop=2, novelty=0.13)],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_II in spans
    assert spans[PHASE_II].start_loop <= spans[PHASE_II].end_loop


def test_phase_ii_does_not_fire_on_single_loop_dip():
    """DET-FAL T5: single-loop dip must NOT fire Phase II."""
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=10, dup=0.05, op="T3"),
               _step(1, novel=1, dup=0.45),
               _step(2, novel=9, dup=0.10),
               _step(3, novel=1, dup=0.40),
               _step(4, novel=10, dup=0.08)],
        en_events=[_en(1, 0.22), _en(3, 0.18)],
    )
    assert PHASE_II not in [p.name for p in detect_phases(traj).phases]


def test_phase_v_closes_on_reversal():
    """DET-FAL T9."""
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=3, dup=0.30),
            _step(2, novel=1, dup=0.55),
            _step(3, novel=0, dup=0.65),
            _step(4, novel=0, dup=0.75),
            _step(5, novel=8, dup=0.20),
            _step(6, novel=6, dup=0.25),
            _step(7, novel=4, dup=0.30),
        ],
        en_events=[],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_V in spans
    assert spans[PHASE_V].start_loop == 2
    assert spans[PHASE_V].end_loop == 4


def test_phase_ii_fires_without_en_events():
    """DET-FAL T8. Post-cycle-9: persistence satisfied by loops 3+4."""
    traj = Trajectory(
        trajectory_id="t",
        steps=[_step(0, novel=10, dup=0.05, op="T3"),
               _step(1, novel=8, dup=0.10),
               _step(2, novel=4, dup=0.20),
               _step(3, novel=2, dup=0.30),
               _step(4, novel=1, dup=0.45)],
        en_events=[],
    )
    spans = {p.name: p for p in detect_phases(traj).phases}
    assert PHASE_II in spans
    span = spans[PHASE_II]
    assert span.start_loop == 3 and span.end_loop == 3
    assert span.confidence == "low"


def test_phase_iii_requires_confirmed_genuine_en_after_cycle_10():
    """Cycle-10 regression (restored in cycle 11 — omitted from cycle
    10's MCP push by accident). Phase III no longer fires on a
    'genuine_transformation_unconfirmed' EN."""
    traj = Trajectory(
        trajectory_id="t",
        steps=[
            _step(0, novel=11, dup=0.05, op="T3"),
            _step(1, novel=2, dup=0.40),
            _step(2, novel=0, dup=0.50),
            _step(3, novel=0, dup=0.55),
            _step(4, novel=0, dup=0.60),
        ],
        en_events=[ENEvent(
            loop_index=1, persona="h", eni_novelty=0.25,
            eni_non_drift=0.7, eni_admissibility=1.0, admitted=True,
            novel_claims_next=0, dup_rate_before=0.40, dup_rate_after=0.50,
        )],
    )
    from desi.phase_detector import PHASE_III
    assert PHASE_III not in [p.name for p in detect_phases(traj).phases]


# Generalization-loop cycle 2: phase non-overlap post-processor.
def test_phase_clip_eliminates_ii_v_overlap():
    """Pre-cycle-2 Phase II:1-3 and Phase V:1-3 could overlap completely.
    Post-cycle-2 Phase II is clipped to end at 0 (becomes empty) or to
    Phase V.start - 1; either way the spans must not intersect.
    """
    from desi.phase_detector import PHASE_II, PHASE_V
    traj = Trajectory(
        trajectory_id="ii_v_overlap",
        steps=[
            _step(0, novel=10, dup=0.05),
            _step(1, novel=1, dup=0.55),
            _step(2, novel=0, dup=0.60),
            _step(3, novel=0, dup=0.65),
            _step(4, novel=6, dup=0.20),
        ],
        en_events=[],
    )
    spans = {p.name: (p.start_loop, p.end_loop) for p in detect_phases(traj).phases}
    if PHASE_II in spans and PHASE_V in spans:
        ii_s, ii_e = spans[PHASE_II]
        v_s, v_e = spans[PHASE_V]
        assert ii_e < v_s, f"Phase II:{ii_s}-{ii_e} must end before Phase V:{v_s}-{v_e}"


def test_phase_clip_preserves_non_overlapping_spans():
    """Cycle 2 must not modify already-non-overlapping spans."""
    from desi.phase_detector import PHASE_I
    traj = Trajectory(
        trajectory_id="no_overlap",
        steps=[_step(0, novel=12, dup=0.05, op="T3")],
        en_events=[],
    )
    phases = detect_phases(traj).phases
    p1 = next(p for p in phases if p.name == PHASE_I)
    assert (p1.start_loop, p1.end_loop) == (0, 0)
