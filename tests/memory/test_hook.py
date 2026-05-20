"""Tests for MemoryHook — recording, error isolation, strict mode."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from desi.memory import (
    HookError,
    InMemoryStore,
    MemoryHook,
    MemoryRecorder,
    RelationType,
)
from desi.models import Trajectory, TrajectoryStep
from desi.runner import run_desi


def _trajectory() -> Trajectory:
    return Trajectory(
        trajectory_id="t_v03_hook",
        steps=[
            TrajectoryStep(loop_index=0, operator="T1",
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


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


def test_hook_records_run_with_trajectory_label() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model="claude-opus-4-7",
                      config={"seed": 7})
    run_desi(_trajectory(), memory_hook=hook)
    # The run was written under a derived run_id.
    runs = list(store._runs.values())
    assert len(runs) == 1
    assert runs[0].label == "t_v03_hook"
    assert runs[0].metadata["model"] == "claude-opus-4-7"
    assert runs[0].metadata["config_hash"]
    assert runs[0].finished_at is not None


def test_hook_records_one_operator_event_per_step() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model="m")
    run_desi(_trajectory(), memory_hook=hook)
    assert len(store._events) == 4
    ops = sorted([e.operator_code for e in store._events.values()])
    assert ops == ["T1", "T2", "T6", "T8"]


def test_hook_records_distinct_claims_for_distinct_focus_ids() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model="m")
    run_desi(_trajectory(), memory_hook=hook)
    # The trajectory touches C001, C002 (twice), C003 — three distinct.
    assert set(store._claims.keys()) == {"C001", "C002", "C003"}


def test_hook_records_derives_from_when_focus_changes() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model="m")
    run_desi(_trajectory(), memory_hook=hook)
    # Steps: C001 -> C002 -> C002 -> C003
    # Focus changes at step 1 (C001->C002) and step 3 (C002->C003).
    derives = [r for r in store._relations
               if r.rel_type is RelationType.DERIVES_FROM]
    assert len(derives) == 2
    pairs = {(r.target_claim_id, r.source_claim_id) for r in derives}
    assert pairs == {("C001", "C002"), ("C002", "C003")}


def test_hook_marks_run_finished_at_end() -> None:
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m")
    run_desi(_trajectory(), memory_hook=hook)
    assert rec.active_run is None  # end_run ran


# ---------------------------------------------------------------------------
# Error isolation (default strict=False)
# ---------------------------------------------------------------------------


def test_hook_isolates_recorder_failure_during_step() -> None:
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m")

    real_record_event = rec.record_operator_event

    def fail_on_third_event(**kwargs):
        if kwargs.get("loop_index") == 2:
            raise RuntimeError("simulated DB outage")
        return real_record_event(**kwargs)

    with patch.object(rec, "record_operator_event",
                      side_effect=fail_on_third_event):
        # Run must succeed despite the recorder error.
        report = run_desi(_trajectory(), memory_hook=hook)
    assert report.trajectory_id == "t_v03_hook"
    # Exactly one captured error on the hook.
    matching = [e for e in hook.errors
                if isinstance(e, HookError) and e.stage == "on_step.operator_event"]
    assert matching, "expected the failed step to be captured"


def test_hook_isolates_recorder_failure_during_run_start() -> None:
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m")
    with patch.object(rec, "start_run",
                      side_effect=RuntimeError("backend down")):
        # The run still produces a report.
        report = run_desi(_trajectory(), memory_hook=hook)
    assert report.n_steps == 4
    # The hook captured the failure; subsequent step calls were skipped.
    start_errors = [e for e in hook.errors if e.stage == "on_run_start"]
    assert len(start_errors) == 1


def test_hook_keeps_errors_in_order_of_occurrence() -> None:
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m")

    real_record_event = rec.record_operator_event
    fail_loops = {1, 3}

    def selective(**kwargs):
        if kwargs.get("loop_index") in fail_loops:
            raise RuntimeError("flaky")
        return real_record_event(**kwargs)

    with patch.object(rec, "record_operator_event", side_effect=selective):
        run_desi(_trajectory(), memory_hook=hook)
    indices = [e.payload.get("loop_index") for e in hook.errors
               if e.stage == "on_step.operator_event"]
    assert indices == [1, 3]


# ---------------------------------------------------------------------------
# Strict mode
# ---------------------------------------------------------------------------


def test_strict_mode_raises_on_recorder_error() -> None:
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m", strict=True)
    with patch.object(rec, "record_operator_event",
                      side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            run_desi(_trajectory(), memory_hook=hook)
    # Error is still captured before it was re-raised.
    assert any(e.exception.args[0] == "boom" for e in hook.errors)


def test_strict_default_is_false() -> None:
    hook = MemoryHook(MemoryRecorder(InMemoryStore()), model="m")
    assert hook.strict is False


# ---------------------------------------------------------------------------
# Optionality / no leakage into result
# ---------------------------------------------------------------------------


def test_run_without_hook_writes_nothing_to_a_recorder() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)  # built but not handed to the runner
    run_desi(_trajectory())
    assert store._claims == {}
    assert store._relations == []
    assert store._runs == {}
    assert store._events == {}
    assert rec.active_run is None
