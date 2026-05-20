"""v3.27 — rollback action.

The closed action set gains one new kind:

* ``rollback_last_transition`` — when the policy fires
  at index ``i``, the counterfactual replaces every
  state from ``i`` onward with a copy of ``states[i-1]``.
  Semantically: "stop where you were one step ago and
  do not proceed". This is the only v3.27 action that
  changes the trajectory's *final* state, which is
  necessary to "rescue" a trajectory that would have
  ended in REJECTED.

Constraints unchanged from v3.26: no rule changes, no
frame overrides, no causal overrides. The action only
re-shapes existing state vectors; it does not call any
runtime logic.
"""
from __future__ import annotations

from enum import Enum

from ..epistemic_trajectory.state import StateVector


class RollbackKind(str, Enum):
    """Closed extension of the v3.26 ActionKind set."""

    ROLLBACK_LAST_TRANSITION = "rollback_last_transition"


def apply_rollback_last_transition(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Roll back the last transition relative to state
    index ``at``. The counterfactual is:

        states[0..at-1] + states[at-1] * (n - at)

    i.e. every state from ``at`` onward is replaced by a
    copy of the state one step earlier. If ``at <= 0`` we
    can't roll back (no prior state), so the trajectory
    is returned unchanged.
    """
    n = len(states)
    if at <= 0 or at >= n:
        return states
    anchor = states[at - 1]
    out = list(states[: at])
    for _ in range(n - at):
        out.append(anchor)
    return tuple(out)


__all__ = [
    "RollbackKind", "apply_rollback_last_transition",
]
