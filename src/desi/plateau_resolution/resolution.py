"""v3.33 — plateau resolution strategy dispatch.

Closed enum of strategies (directive). Each strategy
returns the counterfactual state sequence and a
``Resolution`` outcome record.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.metrics import compute_metrics
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from .escalation import (
    apply_cause_specific_escalation,
    apply_extra_audit_stages,
)
from .hold_extension import apply_extra_confidence_hold


_IDX_SUPPORT = DIMENSION_NAMES.index("support_state")
_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0
_REJECTED        = 3.0


class StrategyKind(str, Enum):
    STRATEGY_A_NO_CHANGE              = "A_no_change"
    STRATEGY_B_EXTRA_CONFIDENCE_HOLD  = "B_extra_confidence_hold"
    STRATEGY_C_EXTRA_AUDIT_STAGES     = "C_extra_audit_stages"
    STRATEGY_D_CAUSE_SPECIFIC         = "D_cause_specific"


@dataclass(frozen=True)
class Resolution:
    trajectory_id: str
    strategy: str                    # StrategyKind value
    original_final_support: float
    counterfactual_final_support: float
    resolved: bool                   # final no longer 2.0
    overcontrol: bool                # SUPPORTED -> not SUPPORTED
    smoothness_pre: float
    smoothness_post: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "strategy": self.strategy,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "resolved": self.resolved,
            "overcontrol": self.overcontrol,
            "smoothness_pre": self.smoothness_pre,
            "smoothness_post": self.smoothness_post,
        }


_DISPATCH = {
    StrategyKind.STRATEGY_A_NO_CHANGE.value:
        lambda s: s,
    StrategyKind.STRATEGY_B_EXTRA_CONFIDENCE_HOLD.value:
        apply_extra_confidence_hold,
    StrategyKind.STRATEGY_C_EXTRA_AUDIT_STAGES.value:
        apply_extra_audit_stages,
    StrategyKind.STRATEGY_D_CAUSE_SPECIFIC.value:
        apply_cause_specific_escalation,
}


def apply_strategy(
    states: tuple[StateVector, ...], strategy: str,
) -> tuple[StateVector, ...]:
    fn = _DISPATCH.get(strategy)
    if fn is None:
        return states
    return fn(states)


def resolve_one(
    traj: Trajectory, strategy: str,
) -> Resolution:
    original_final = traj.states[-1].support_state
    cf = apply_strategy(traj.states, strategy)
    cf_final = cf[-1].support_state
    resolved = (
        original_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
    )
    overcontrol = (
        original_final == _SUPPORTED
        and cf_final != _SUPPORTED
    )
    pre_metric = compute_metrics(
        f"{traj.trajectory_id}:pre", traj.states,
    )
    post_metric = compute_metrics(
        f"{traj.trajectory_id}:post", cf,
    )
    return Resolution(
        trajectory_id=traj.trajectory_id,
        strategy=strategy,
        original_final_support=original_final,
        counterfactual_final_support=cf_final,
        resolved=resolved, overcontrol=overcontrol,
        smoothness_pre=pre_metric.smoothness,
        smoothness_post=post_metric.smoothness,
    )


def resolve_all_strategies(
    traj: Trajectory,
) -> tuple[Resolution, ...]:
    return tuple(
        resolve_one(traj, k.value)
        for k in StrategyKind
    )


__all__ = [
    "Resolution", "StrategyKind", "apply_strategy",
    "resolve_all_strategies", "resolve_one",
]
