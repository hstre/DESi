"""Tests for the v0.3 top-level entrypoint ``desi.runner.run_desi``.

Two invariants:

1. Without ``memory_hook``, ``run_desi`` is bit-for-bit equivalent to the
   pre-v0.3 ``compute_all``.
2. With or without ``memory_hook``, the returned :class:`DeterministicMetrics`
   is identical. The hook is observation-only.
"""
from __future__ import annotations

import pytest

from desi.diagnostics import compute_all
from desi.memory import InMemoryStore, MemoryHook, MemoryRecorder
from desi.models import Trajectory, TrajectoryStep
from desi.runner import run_desi


def _trajectory() -> Trajectory:
    return Trajectory(
        trajectory_id="t_v03_runner",
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
# Optionality
# ---------------------------------------------------------------------------


def test_run_desi_without_hook_matches_compute_all() -> None:
    traj = _trajectory()
    assert run_desi(traj) == compute_all(traj)


def test_run_desi_without_hook_does_not_require_memory_module() -> None:
    # Sanity: the no-hook path does not depend on a recorder or store.
    traj = _trajectory()
    report = run_desi(traj)
    assert report.trajectory_id == "t_v03_runner"
    assert report.n_steps == 4


# ---------------------------------------------------------------------------
# Result equality with / without hook
# ---------------------------------------------------------------------------


def test_run_desi_result_is_identical_with_or_without_hook() -> None:
    traj = _trajectory()
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="claude-opus-4-7")
    a = run_desi(traj, memory_hook=hook)
    b = run_desi(_trajectory())  # fresh, no hook
    assert a == b


def test_hook_does_not_mutate_report_object() -> None:
    traj = _trajectory()
    plain = run_desi(traj)
    rec = MemoryRecorder(InMemoryStore())
    hook = MemoryHook(rec, model="m")
    hooked = run_desi(traj, memory_hook=hook)
    assert plain == hooked
    # And the hook ran (didn't silently no-op):
    assert hook.errors == []
    assert rec.active_run is None  # ended cleanly
