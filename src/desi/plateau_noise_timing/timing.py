"""v3.36 — timing perturbation.

Apply ``+1 confidence_hold + audit withdraw`` at four
distinct timing points relative to the audit step:

* t-1            — index ``n-2`` (immediately before
                   audit)
* t-2            — index ``n-3`` (matches v3.34
                   Strategy B / v3.33 Strategy B)
* t-3            — index ``n-4`` (one step earlier)
* after_audit    — index ``n-1`` (the audit step
                   itself); the hold has no later
                   states to clamp and the audit
                   withdrawal is a no-op since there
                   is no "audit step" after this index.

The resolution count per timing point tells us whether
the plateau resolution requires a specific timing or
any pre-audit timing works.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..cause_aware_control.actions import (
    apply_confidence_hold,
)
from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.state import StateVector


_BRIDGE_REQUIRED = 2.0


class TimingPoint(str, Enum):
    T_MINUS_1   = "t_minus_1"
    T_MINUS_2   = "t_minus_2"
    T_MINUS_3   = "t_minus_3"
    AFTER_AUDIT = "after_audit"


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


def _index_for(
    timing: str, n: int,
) -> int | None:
    if timing == TimingPoint.T_MINUS_1.value:
        return n - 2
    if timing == TimingPoint.T_MINUS_2.value:
        return n - 3
    if timing == TimingPoint.T_MINUS_3.value:
        return n - 4
    if timing == TimingPoint.AFTER_AUDIT.value:
        return None      # no pre-audit intervention
    return None


def apply_timed_hold(
    states: tuple[StateVector, ...], timing: str,
) -> tuple[StateVector, ...]:
    n = len(states)
    idx = _index_for(timing, n)
    if idx is None:
        # AFTER_AUDIT: hold cannot apply pre-audit and
        # the audit step has already committed. Return
        # the original trajectory unchanged.
        return states
    if idx < 1 or idx >= n - 1:
        # Index out of range or AT/PAST audit -> the
        # confidence_hold has nothing to clamp; we still
        # return the unmodified trajectory rather than
        # withdrawing the audit step, because the
        # timing point did not deliver any holding
        # action.
        return states
    held = apply_confidence_hold(states, idx)
    return _withdraw_audit_step(held)


@dataclass(frozen=True)
class TimingOutcome:
    trajectory_id: str
    timing: str
    original_final_support: float
    counterfactual_final_support: float
    resolved: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "timing": self.timing,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "resolved": self.resolved,
        }


def run_timing(
    traj: Trajectory, timing: str,
) -> TimingOutcome:
    cf = apply_timed_hold(traj.states, timing)
    orig = traj.states[-1].support_state
    new_final = cf[-1].support_state
    resolved = (
        orig == _BRIDGE_REQUIRED
        and new_final != _BRIDGE_REQUIRED
    )
    return TimingOutcome(
        trajectory_id=traj.trajectory_id,
        timing=timing,
        original_final_support=orig,
        counterfactual_final_support=new_final,
        resolved=resolved,
    )


def all_timing_outcomes(
    trajectories: tuple[Trajectory, ...],
) -> tuple[TimingOutcome, ...]:
    out: list[TimingOutcome] = []
    for t in trajectories:
        for k in TimingPoint:
            out.append(run_timing(t, k.value))
    return tuple(out)


__all__ = [
    "TimingOutcome", "TimingPoint", "all_timing_outcomes",
    "apply_timed_hold", "run_timing",
]
