"""v3.35 — apply Strategy B (+1 confidence_hold) to
the non-plateau cliff classes and measure cross-class
effects.

The directive's cross-class universe:

* 20 plateau (CONFIDENCE_OSCILLATION + final 2.0)
* 14 CAUSAL_LEAP (final 3.0)
* 2  SUPPORT_DECAY (final 1.0)
* 0  FRAME_COLLISION (empirical: zero in current corpus
  after the v3.28 hash-seed-stable signal definition)

Strategy B is the v3.34 ``B1_ONE_HOLD`` action: one
extra confidence_hold at index ``n-3`` followed by an
audit-step withdrawal.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.state import StateVector
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from ..trajectory_root_cause.cause import CauseClass
from ..trajectory_root_cause.classifier import (
    classify_trajectory,
)


_BRIDGE_REQUIRED  = 2.0
_REJECTED         = 3.0
_SUPPORTED        = 4.0


class TargetClass(str, Enum):
    PLATEAU         = "plateau"
    CAUSAL_LEAP     = "causal_leap"
    SUPPORT_DECAY   = "support_decay"
    FRAME_COLLISION = "frame_collision"


@dataclass(frozen=True)
class CrossClassOutcome:
    trajectory_id: str
    target_class: str           # TargetClass value
    primary_cause: str          # CauseClass value
    original_final_support: float
    counterfactual_final_support: float
    changed: bool
    resolved_plateau: bool      # only meaningful for
                                # the plateau group
    false_rescue: bool          # REJECTED -> not REJECTED
    overcontrol: bool           # SUPPORTED -> not SUPPORTED

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "target_class": self.target_class,
            "primary_cause": self.primary_cause,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "changed": self.changed,
            "resolved_plateau": self.resolved_plateau,
            "false_rescue": self.false_rescue,
            "overcontrol": self.overcontrol,
        }


def _classify_target(
    traj: Trajectory, plateau_ids: set,
) -> tuple[str, str]:
    primary = classify_trajectory(traj).primary_cause
    if traj.trajectory_id in plateau_ids:
        return TargetClass.PLATEAU.value, primary
    if primary == CauseClass.CAUSAL_LEAP.value:
        return TargetClass.CAUSAL_LEAP.value, primary
    if primary == CauseClass.SUPPORT_DECAY.value:
        return TargetClass.SUPPORT_DECAY.value, primary
    if primary == CauseClass.FRAME_COLLISION.value:
        return TargetClass.FRAME_COLLISION.value, primary
    return primary, primary  # not part of the universe


def _apply_strategy_b(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    return apply_k_holds(states, 1)


def run_one(
    traj: Trajectory, target_class: str, primary: str,
) -> CrossClassOutcome:
    cf = _apply_strategy_b(traj.states)
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    changed = orig_final != cf_final
    resolved_plateau = (
        target_class == TargetClass.PLATEAU.value
        and orig_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
    )
    false_rescue = (
        target_class != TargetClass.PLATEAU.value
        and orig_final == _REJECTED
        and cf_final != _REJECTED
    )
    overcontrol = (
        orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
    )
    return CrossClassOutcome(
        trajectory_id=traj.trajectory_id,
        target_class=target_class,
        primary_cause=primary,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        changed=changed,
        resolved_plateau=resolved_plateau,
        false_rescue=false_rescue,
        overcontrol=overcontrol,
    )


def collect_universe(
) -> tuple[CrossClassOutcome, ...]:
    plateau_ids = set(plateau_trajectory_ids())
    targets = {
        TargetClass.PLATEAU.value,
        TargetClass.CAUSAL_LEAP.value,
        TargetClass.SUPPORT_DECAY.value,
        TargetClass.FRAME_COLLISION.value,
    }
    out: list[CrossClassOutcome] = []
    for t in extract_all_trajectories():
        tc, pc = _classify_target(t, plateau_ids)
        if tc not in targets:
            continue
        out.append(run_one(t, tc, pc))
    return tuple(out)


def per_class_counts(
    outcomes: tuple[CrossClassOutcome, ...],
) -> dict[str, int]:
    return dict(Counter(o.target_class for o in outcomes))


__all__ = [
    "CrossClassOutcome", "TargetClass",
    "collect_universe", "per_class_counts", "run_one",
]
