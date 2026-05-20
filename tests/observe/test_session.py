"""Tests for ObservationSession — recording + ordering + determinism."""
from __future__ import annotations

from desi.memory import InMemoryStore, MemoryRecorder, RelationType
from desi.models import Trajectory, TrajectoryStep
from desi.observe import EventType, ObservationSession
from desi.runner import run_desi


def _trajectory() -> Trajectory:
    return Trajectory(
        trajectory_id="t_obs",
        steps=[
            TrajectoryStep(loop_index=0, operator="T6",
                            focus_claim_id="C001"),
            TrajectoryStep(loop_index=1, operator="T6",
                            focus_claim_id="C002"),
            TrajectoryStep(loop_index=2, operator="T2",
                            focus_claim_id="C002"),
            TrajectoryStep(loop_index=3, operator="T8",
                            focus_claim_id="C003"),
        ],
        en_events=[],
    )


def _session(seed: int = 0) -> ObservationSession:
    return ObservationSession(MemoryRecorder(InMemoryStore()),
                              model="m", seed=seed)


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------


def test_session_emits_run_started_and_run_ended() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    types = [e.event_type for e in sess.events]
    assert types[0] is EventType.RUN_STARTED
    assert types[-1] is EventType.RUN_ENDED


def test_session_emits_operator_started_and_ended_per_step() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    starts = [e for e in sess.events
              if e.event_type is EventType.OPERATOR_STARTED]
    ends = [e for e in sess.events
            if e.event_type is EventType.OPERATOR_ENDED]
    assert len(starts) == 4
    assert len(ends) == 4


def test_session_emits_claim_created_per_distinct_focus() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    cc = [e for e in sess.events
          if e.event_type is EventType.CLAIM_CREATED]
    ids = [e.payload["claim_id"] for e in cc]
    assert ids == ["C001", "C002", "C003"]


def test_session_emits_branch_opened_for_each_new_focus() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    bo = [e for e in sess.events
          if e.event_type is EventType.BRANCH_OPENED]
    assert [e.payload["focus_claim_id"] for e in bo] == ["C001", "C002", "C003"]


def test_session_closes_open_branches_at_run_end() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    bc = [e for e in sess.events
          if e.event_type is EventType.BRANCH_CLOSED]
    # One closed mid-run on the C001->C002 transition;
    # the C003 branch is closed at run_end.
    closed_focus = [e.payload["focus_claim_id"] for e in bc]
    assert "C001" in closed_focus
    assert "C003" in closed_focus


def test_session_emits_relation_created_on_focus_change() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    rels = [e for e in sess.events
            if e.event_type is EventType.RELATION_CREATED]
    types = [e.payload["rel_type"] for e in rels]
    assert all(t == RelationType.DERIVES_FROM.value for t in types)
    # C001->C002 and C002->C003 are the two focus shifts.
    assert len(rels) == 2


# ---------------------------------------------------------------------------
# Ordering and determinism
# ---------------------------------------------------------------------------


def test_ticks_are_monotonic_and_dense() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    ticks = [e.tick for e in sess.events]
    assert ticks == sorted(ticks)
    assert ticks == list(range(len(ticks)))


def test_two_runs_with_same_input_produce_identical_timelines() -> None:
    a = _session(seed=7)
    run_desi(_trajectory(), memory_hook=a.hook)
    b = _session(seed=7)
    run_desi(_trajectory(), memory_hook=b.hook)
    # Equality excludes wall-clock ts (TimelineEvent compare=False on ts).
    assert a.events == b.events


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


def test_session_takes_start_and_end_snapshots() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    labels = [s.label for s in sess.snapshots]
    assert labels[0] == "start"
    assert labels[-1] == "end"


def test_end_snapshot_contains_all_recorded_claims() -> None:
    sess = _session()
    run_desi(_trajectory(), memory_hook=sess.hook)
    end = sess.snapshots[-1]
    claim_ids = {c["claim_id"] for c in end.claims}
    assert claim_ids == {"C001", "C002", "C003"}
