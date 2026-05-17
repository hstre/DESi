"""v3.29 — four counterfactual run variants.

For every trajectory that v3.27 rolled back, compute the
final state vector and trajectory geometry under four
controller configurations:

* RUN_A — Normal DESi (v3.27 controller with rollback).
* RUN_B — Rollback disabled (v3.26 passive controller).
* RUN_C — All pruning / intervention disabled
  (no controller; trajectory carries its original
  state sequence).
* RUN_D — Delayed closure (the audit step is removed;
  the trajectory is truncated before the final
  transition).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.metrics import compute_metrics
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector, TrajectorySource,
)
from ..trajectory_control.controller import (
    control_trajectory,
)
from ..trajectory_control.replay_control import (
    control_with_rollback,
)


_IDX_BRANCH  = DIMENSION_NAMES.index("branch_cost")
_IDX_SUPPORT = DIMENSION_NAMES.index("support_state")
_IDX_CONTRA  = DIMENSION_NAMES.index(
    "contradiction_load",
)


class RunKind(str, Enum):
    RUN_A_NORMAL          = "RUN_A_NORMAL"
    RUN_B_NO_ROLLBACK     = "RUN_B_NO_ROLLBACK"
    RUN_C_NO_PRUNING      = "RUN_C_NO_PRUNING"
    RUN_D_DELAYED_CLOSURE = "RUN_D_DELAYED_CLOSURE"


@dataclass(frozen=True)
class RunOutcome:
    trajectory_id: str
    run: str                    # RunKind value
    final_support_state: float
    final_branch_cost: float
    final_contradiction_load: float
    support_depth: float        # max support reached
    smoothness: float
    replay_hash: str            # canonical hash of states

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "run": self.run,
            "final_support_state":
                self.final_support_state,
            "final_branch_cost":
                self.final_branch_cost,
            "final_contradiction_load":
                self.final_contradiction_load,
            "support_depth": self.support_depth,
            "smoothness": self.smoothness,
            "replay_hash": self.replay_hash,
        }


def _hash_states(
    states: tuple[StateVector, ...],
) -> str:
    payload = [s.to_dict() for s in states]
    canon = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canon).hexdigest()[:16]


def _outcome(
    traj_id: str, run: RunKind,
    states: tuple[StateVector, ...],
) -> RunOutcome:
    if not states:
        return RunOutcome(
            trajectory_id=traj_id, run=run.value,
            final_support_state=0.0,
            final_branch_cost=0.0,
            final_contradiction_load=0.0,
            support_depth=0.0,
            smoothness=0.0,
            replay_hash=_hash_states(states),
        )
    final = states[-1].to_tuple()
    supps = [s.to_tuple()[_IDX_SUPPORT] for s in states]
    metric = compute_metrics(traj_id, states)
    return RunOutcome(
        trajectory_id=traj_id, run=run.value,
        final_support_state=final[_IDX_SUPPORT],
        final_branch_cost=final[_IDX_BRANCH],
        final_contradiction_load=final[_IDX_CONTRA],
        support_depth=max(supps),
        smoothness=metric.smoothness,
        replay_hash=_hash_states(states),
    )


def run_a_normal(traj: Trajectory) -> RunOutcome:
    """v3.27 controller — rollback enabled."""
    outcome = control_with_rollback(traj)
    # Reconstruct counterfactual states by applying the
    # chosen action.
    from ..trajectory_control.replay_control import (
        _apply_action_with_rollback,
    )
    states = traj.states
    for entry in outcome.trace.entries:
        if entry.action != "no_action":
            states = _apply_action_with_rollback(
                states, entry.action, entry.state_index,
            )
            break
    return _outcome(
        traj.trajectory_id, RunKind.RUN_A_NORMAL, states,
    )


def run_b_no_rollback(traj: Trajectory) -> RunOutcome:
    """v3.26 controller — passive actions, no rollback."""
    outcome = control_trajectory(traj)
    from ..trajectory_control.actions import apply_action
    states = traj.states
    for action in outcome.applied_actions:
        states = apply_action(
            states, action.action,
            action.intervention_index,
        )
        break  # one-shot, like v3.26
    return _outcome(
        traj.trajectory_id, RunKind.RUN_B_NO_ROLLBACK,
        states,
    )


def run_c_no_pruning(traj: Trajectory) -> RunOutcome:
    """No controller — trajectory unchanged."""
    return _outcome(
        traj.trajectory_id, RunKind.RUN_C_NO_PRUNING,
        traj.states,
    )


def run_d_delayed_closure(traj: Trajectory) -> RunOutcome:
    """Audit step removed — trajectory truncated to the
    pre-audit state. Captures 'what if we never
    committed to a verdict at all'."""
    if len(traj.states) <= 1:
        states = traj.states
    else:
        states = traj.states[:-1]
    return _outcome(
        traj.trajectory_id, RunKind.RUN_D_DELAYED_CLOSURE,
        states,
    )


def all_runs(
    traj: Trajectory,
) -> tuple[RunOutcome, ...]:
    return (
        run_a_normal(traj),
        run_b_no_rollback(traj),
        run_c_no_pruning(traj),
        run_d_delayed_closure(traj),
    )


def rollback_trajectory_ids() -> tuple[str, ...]:
    """Identify trajectories the v3.27 controller would
    roll back. Pulled deterministically from the live
    controller (no artifact pin needed)."""
    from ..trajectory_control.replay_control import (
        control_all_with_rollback,
    )
    trajs = extract_all_trajectories()
    outcomes = control_all_with_rollback(trajs)
    return tuple(
        o.trajectory_id for o in outcomes if o.rolled_back
    )


__all__ = [
    "RunKind", "RunOutcome", "all_runs",
    "rollback_trajectory_ids", "run_a_normal",
    "run_b_no_rollback", "run_c_no_pruning",
    "run_d_delayed_closure",
]
