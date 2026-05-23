"""v3.26 — passive intervention actions.

Closed enumeration. Every action is a *simulation*:
given a trajectory and an intervention point, the action
produces a counterfactual trajectory that the action
would have produced if applied. No runtime state, no
rule changes, no frame overrides, no causal overrides —
the actions only re-shape downstream state vectors of
the same trajectory.

Three closed kinds:

* ``branch_freeze``  — clamp the branch_cost dimension
  of every state s_{i+1}..s_{n-1} at the value it had at
  the intervention point. Models a deliberate decision
  to stop enumerating new premises.
* ``forced_replay``  — re-route through the same state
  reading by zeroing transition novelty for one step
  past the intervention point. Models "replay this step
  without taking the new branch."
* ``confidence_hold`` — clamp confidence at every later
  state to the maximum of (current value, intervention-
  point value), so confidence may not decay further.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


class ActionKind(str, Enum):
    BRANCH_FREEZE   = "branch_freeze"
    FORCED_REPLAY   = "forced_replay"
    CONFIDENCE_HOLD = "confidence_hold"


_IDX_FRAME    = DIMENSION_NAMES.index("frame_id")
_IDX_CONF     = DIMENSION_NAMES.index("confidence")
_IDX_BRANCH   = DIMENSION_NAMES.index("branch_cost")
_IDX_SUPPORT  = DIMENSION_NAMES.index("support_state")
_IDX_NOVELTY  = DIMENSION_NAMES.index("novelty")


@dataclass(frozen=True)
class AppliedAction:
    """Record of an action and where it landed."""

    action: str            # ActionKind value
    intervention_index: int

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "intervention_index": self.intervention_index,
        }


def _replace(
    s: StateVector, **updates,
) -> StateVector:
    d = s.to_dict()
    d.update(updates)
    return StateVector(**d)


def apply_branch_freeze(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Clamp branch_cost ≤ s[at].branch_cost from index
    at+1 onwards."""
    if at >= len(states) - 1:
        return states
    clamp = states[at].branch_cost
    out = list(states[: at + 1])
    for s in states[at + 1:]:
        new_branch = min(s.branch_cost, clamp)
        out.append(_replace(s, branch_cost=new_branch))
    return tuple(out)


def apply_confidence_hold(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Confidence may not decay below s[at].confidence
    from index at+1 onwards."""
    if at >= len(states) - 1:
        return states
    floor = states[at].confidence
    out = list(states[: at + 1])
    for s in states[at + 1:]:
        new_conf = max(s.confidence, floor)
        out.append(_replace(s, confidence=new_conf))
    return tuple(out)


def apply_forced_replay(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Zero out novelty for the transition at+1 (i.e.
    replay the next step without taking the new branch)."""
    if at >= len(states) - 1:
        return states
    out = list(states[: at + 1])
    s_next = states[at + 1]
    out.append(_replace(s_next, novelty=0.0))
    out.extend(states[at + 2:])
    return tuple(out)


_DISPATCH = {
    ActionKind.BRANCH_FREEZE.value:   apply_branch_freeze,
    ActionKind.CONFIDENCE_HOLD.value: apply_confidence_hold,
    ActionKind.FORCED_REPLAY.value:   apply_forced_replay,
}


def apply_action(
    states: tuple[StateVector, ...], action: str, at: int,
) -> tuple[StateVector, ...]:
    fn = _DISPATCH.get(action)
    if fn is None:
        return states
    return fn(states, at)


__all__ = [
    "ActionKind", "AppliedAction", "apply_action",
    "apply_branch_freeze", "apply_confidence_hold",
    "apply_forced_replay",
]
