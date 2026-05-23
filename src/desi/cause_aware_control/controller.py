"""v3.30 — cause-aware controller.

The classifier (v3.28) names a primary cause for every
cliff-bearing trajectory. The cause-aware controller
maps the cause to a closed action:

  SUPPORT_DECAY          -> support_hold
  FRAME_COLLISION        -> frame_replay
  BRANCH_OVERLOAD        -> branch_prune
  CAUSAL_LEAP            -> causal_suspend
  CONFIDENCE_OSCILLATION -> confidence_hold
  UNKNOWN                -> rollback_last_transition

The intervention point is the final-transition index
(``n - 2``), because that is the only point where the
action can change the audit verdict; cause-specific
actions clamp the relevant dimension through the audit
step.

NCs are still observed and classified (the v3.28
classifier returns UNKNOWN on every NC). UNKNOWN +
no-cliff is treated as "do nothing" — the controller
never triggers on NCs.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from ..trajectory_control.observer import observe
from ..trajectory_root_cause.cause import CauseClass
from ..trajectory_root_cause.classifier import (
    classify_trajectory,
)
from .actions import CauseActionKind, apply_cause_action


_IDX_SUPPORT = DIMENSION_NAMES.index("support_state")
_REJECTED = 3.0
_SUPPORTED = 4.0


_CAUSE_TO_ACTION: dict[str, str] = {
    CauseClass.SUPPORT_DECAY.value:
        CauseActionKind.SUPPORT_HOLD.value,
    CauseClass.FRAME_COLLISION.value:
        CauseActionKind.FRAME_REPLAY.value,
    CauseClass.BRANCH_OVERLOAD.value:
        CauseActionKind.BRANCH_PRUNE.value,
    CauseClass.CAUSAL_LEAP.value:
        CauseActionKind.CAUSAL_SUSPEND.value,
    CauseClass.CONFIDENCE_OSCILLATION.value:
        CauseActionKind.CONFIDENCE_HOLD.value,
    CauseClass.UNKNOWN.value:
        CauseActionKind.ROLLBACK_LAST_TRANSITION.value,
}


@dataclass(frozen=True)
class CauseAwareOutcome:
    trajectory_id: str
    source: str
    cause: str
    action: str | None        # CauseActionKind value
    original_final_support: float
    counterfactual_final_support: float
    intervened: bool
    rescued: bool
    overcontrol: bool
    used_rollback: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "cause": self.cause,
            "action": self.action,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "intervened": self.intervened,
            "rescued": self.rescued,
            "overcontrol": self.overcontrol,
            "used_rollback": self.used_rollback,
        }


def control_trajectory(traj: Trajectory) -> CauseAwareOutcome:
    obs = observe(traj)
    has_cliff = obs.cliff_count > 0
    assignment = classify_trajectory(traj)
    cause = assignment.primary_cause
    action = (
        _CAUSE_TO_ACTION.get(cause) if has_cliff else None
    )
    # No cliff -> no intervention (matches v3.28's NC
    # discipline).
    states = traj.states
    n = len(states)
    intervened = False
    used_rollback = False
    if action is not None and n >= 2:
        at = n - 2
        states = apply_cause_action(states, action, at)
        intervened = True
        used_rollback = (
            action == CauseActionKind.ROLLBACK_LAST_TRANSITION.value
        )
    original_final = traj.states[-1].support_state
    cf_final = states[-1].support_state
    rescued = (
        original_final == _REJECTED
        and cf_final != _REJECTED
        and intervened
    )
    overcontrol = (
        original_final == _SUPPORTED
        and cf_final != _SUPPORTED
        and intervened
    )
    return CauseAwareOutcome(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value, cause=cause,
        action=action,
        original_final_support=original_final,
        counterfactual_final_support=cf_final,
        intervened=intervened, rescued=rescued,
        overcontrol=overcontrol,
        used_rollback=used_rollback,
    )


def control_all(
    trajectories: tuple[Trajectory, ...] | None = None,
) -> tuple[CauseAwareOutcome, ...]:
    trajs = trajectories if trajectories is not None else (
        extract_all_trajectories()
    )
    return tuple(control_trajectory(t) for t in trajs)


__all__ = [
    "CauseAwareOutcome", "control_all",
    "control_trajectory",
]
