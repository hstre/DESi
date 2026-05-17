"""v3.71 — claim-region primitives.

A "region" is a state-vector projection that captures
a meaningful part of claim-space. v3.71 uses two
closed projections:

* ``state_region`` = (frame_id, support_state) — the
  coarse (frame, support) grid; identifies the
  trajectory's resting spot per state.
* ``transition_region`` = (frame_a, support_a,
  frame_b, support_b) — adjacent state pairs;
  identifies which state transitions the trajectory
  makes.
"""
from __future__ import annotations

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)


def state_regions(
    traj: Trajectory,
) -> frozenset[tuple[float, float]]:
    return frozenset(
        (s.frame_id, s.support_state)
        for s in traj.states
    )


def transition_regions(
    traj: Trajectory,
) -> frozenset[
    tuple[float, float, float, float]
]:
    return frozenset(
        (
            traj.states[i].frame_id,
            traj.states[i].support_state,
            traj.states[i + 1].frame_id,
            traj.states[i + 1].support_state,
        )
        for i in range(len(traj.states) - 1)
    )


def all_other_state_regions(
    exclude_id: str,
) -> frozenset[tuple[float, float]]:
    out: set = set()
    for t in extract_all_trajectories():
        if t.trajectory_id == exclude_id:
            continue
        out |= state_regions(t)
    return frozenset(out)


def all_other_transition_regions(
    exclude_id: str,
) -> frozenset[
    tuple[float, float, float, float]
]:
    out: set = set()
    for t in extract_all_trajectories():
        if t.trajectory_id == exclude_id:
            continue
        out |= transition_regions(t)
    return frozenset(out)


__all__ = [
    "all_other_state_regions",
    "all_other_transition_regions",
    "state_regions", "transition_regions",
]
