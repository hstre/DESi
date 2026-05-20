"""v3.34 — hold-length sweep on the plateau set.

Five closed strategies; each composes K extra
confidence_hold actions before withdrawing the audit
step. K = 0 (identity baseline) through K = 4.

Per-strategy outcome:

* ``resolved`` — final support_state moves out of the
  plateau (2.0).
* ``overcontrol`` — original was SUPPORTED but
  counterfactual is not (none of the plateau set is
  originally SUPPORTED, so overcontrol on the plateau
  set is zero by construction; the metric still
  observes it for paranoia).
* ``smoothness_post`` — for diminishing-returns
  measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..cause_aware_control.actions import (
    apply_confidence_hold,
)
from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.metrics import compute_metrics
from ..epistemic_trajectory.state import StateVector


_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0
_UNDER_AUDIT     = 0.0


class HoldStrategy(str, Enum):
    B0_ZERO_HOLDS  = "B0"
    B1_ONE_HOLD    = "B1"
    B2_TWO_HOLDS   = "B2"
    B3_THREE_HOLDS = "B3"
    B4_FOUR_HOLDS  = "B4"


_K_BY_STRATEGY = {
    HoldStrategy.B0_ZERO_HOLDS.value:  0,
    HoldStrategy.B1_ONE_HOLD.value:    1,
    HoldStrategy.B2_TWO_HOLDS.value:   2,
    HoldStrategy.B3_THREE_HOLDS.value: 3,
    HoldStrategy.B4_FOUR_HOLDS.value:  4,
}


def _replace(s: StateVector, **u) -> StateVector:
    d = s.to_dict()
    d.update(u)
    return StateVector(**d)


def _withdraw_audit_step(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    if len(states) < 2:
        return states
    anchor = states[-2].support_state
    return tuple(states[:-1]) + (
        _replace(states[-1], support_state=anchor),
    )


def apply_k_holds(
    states: tuple[StateVector, ...], k: int,
) -> tuple[StateVector, ...]:
    """Apply k extra confidence_hold actions at
    successive earlier indices (n-3, n-4, ..., n-2-k)
    then withdraw the audit step. ``k == 0`` is the
    identity baseline (no hold, no withdraw)."""
    if k <= 0:
        return states
    n = len(states)
    out = states
    for offset in range(1, k + 1):
        at = n - 2 - offset
        if at < 1:
            break
        out = apply_confidence_hold(out, at)
    return _withdraw_audit_step(out)


@dataclass(frozen=True)
class SweepOutcome:
    trajectory_id: str
    strategy: str                       # HoldStrategy value
    k: int
    original_final_support: float
    counterfactual_final_support: float
    resolved: bool
    overcontrol: bool
    smoothness_pre: float
    smoothness_post: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "strategy": self.strategy,
            "k": self.k,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "resolved": self.resolved,
            "overcontrol": self.overcontrol,
            "smoothness_pre": self.smoothness_pre,
            "smoothness_post": self.smoothness_post,
        }


def sweep_one(
    traj: Trajectory, strategy: str,
) -> SweepOutcome:
    k = _K_BY_STRATEGY[strategy]
    cf = apply_k_holds(traj.states, k)
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    resolved = (
        orig_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
    )
    overcontrol = (
        orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
    )
    pre = compute_metrics(
        f"{traj.trajectory_id}:pre", traj.states,
    )
    post = compute_metrics(
        f"{traj.trajectory_id}:post", cf,
    )
    return SweepOutcome(
        trajectory_id=traj.trajectory_id,
        strategy=strategy, k=k,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        resolved=resolved, overcontrol=overcontrol,
        smoothness_pre=pre.smoothness,
        smoothness_post=post.smoothness,
    )


def sweep_all_strategies(
    traj: Trajectory,
) -> tuple[SweepOutcome, ...]:
    return tuple(
        sweep_one(traj, k.value)
        for k in HoldStrategy
    )


__all__ = [
    "HoldStrategy", "SweepOutcome", "apply_k_holds",
    "sweep_all_strategies", "sweep_one",
]
