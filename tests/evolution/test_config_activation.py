"""Tests for v0.7 config activation in run_desi."""
from __future__ import annotations

from desi.memory import InMemoryStore, MemoryRecorder
from desi.models import Trajectory, TrajectoryStep
from desi.observe import EventType, ObservationSession
from desi.runner import run_desi


def _explosion() -> Trajectory:
    return Trajectory(
        trajectory_id="t_v07_cfg",
        steps=[
            TrajectoryStep(loop_index=i, operator="T6",
                            focus_claim_id=f"E{i:02d}")
            for i in range(6)
        ] + [TrajectoryStep(loop_index=6, operator="T2",
                            focus_claim_id="E05")],
        en_events=[],
    )


def _session(seed: int = 42) -> ObservationSession:
    return ObservationSession(MemoryRecorder(InMemoryStore()),
                              model="m", seed=seed)


# ---------------------------------------------------------------------------
# Default + no-config preserves v0.6 behaviour
# ---------------------------------------------------------------------------


def test_run_desi_without_config_is_bit_identical_to_v06() -> None:
    """No config → threshold defaults to 0.0 → every branch opens.

    For the explosion trajectory: 6 distinct foci → 6 branch_opened
    events. No guard_blocked from suppression.
    """
    sess = _session()
    run_desi(_explosion(), memory_hook=sess.hook)
    opens = [e for e in sess.events if e.event_type is EventType.BRANCH_OPENED]
    suppressed = [e for e in sess.events
                  if e.event_type is EventType.GUARD_BLOCKED
                  and e.payload.get("operator") == "branch_open_guard"]
    assert len(opens) == 6
    assert len(suppressed) == 0


def test_run_desi_with_none_config_is_bit_identical_to_no_config() -> None:
    a = _session(seed=42)
    run_desi(_explosion(), memory_hook=a.hook)
    b = _session(seed=42)
    run_desi(_explosion(), config=None, memory_hook=b.hook)
    assert a.events == b.events


# ---------------------------------------------------------------------------
# Stable threshold 0.30 already suppresses tail branches
# ---------------------------------------------------------------------------


def test_run_desi_with_stable_threshold_suppresses_tail_branches() -> None:
    sess = _session()
    cfg = {"guard_thresholds.branch_open_evidence_min": 0.30}
    run_desi(_explosion(), config=cfg, memory_hook=sess.hook)
    opens = [e for e in sess.events if e.event_type is EventType.BRANCH_OPENED]
    blocks = [e for e in sess.events
              if e.event_type is EventType.GUARD_BLOCKED
              and e.payload.get("operator") == "branch_open_guard"]
    # Under stable threshold 0.30 the explosion drops from 6 opens to 4.
    assert len(opens) == 4
    assert len(blocks) == 2


def test_run_desi_with_mutation_threshold_suppresses_more_branches() -> None:
    sess = _session()
    cfg = {"guard_thresholds.branch_open_evidence_min": 0.45}
    run_desi(_explosion(), config=cfg, memory_hook=sess.hook)
    opens = [e for e in sess.events if e.event_type is EventType.BRANCH_OPENED]
    blocks = [e for e in sess.events
              if e.event_type is EventType.GUARD_BLOCKED
              and e.payload.get("operator") == "branch_open_guard"]
    # M-001: 3 opens + 3 suppressions under threshold 0.45.
    assert len(opens) == 3
    assert len(blocks) == 3


def test_threshold_and_evidence_are_visible_on_each_branch_event() -> None:
    sess = _session()
    cfg = {"guard_thresholds.branch_open_evidence_min": 0.45}
    run_desi(_explosion(), config=cfg, memory_hook=sess.hook)
    for e in sess.events:
        if e.event_type is EventType.BRANCH_OPENED:
            assert "evidence" in e.payload
            assert "threshold" in e.payload
            assert e.payload["threshold"] == 0.45
        if (e.event_type is EventType.GUARD_BLOCKED
                and e.payload.get("operator") == "branch_open_guard"):
            assert "evidence" in e.payload
            assert "threshold" in e.payload
