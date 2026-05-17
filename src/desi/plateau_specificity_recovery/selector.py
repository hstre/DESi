"""v3.39 — closed-set selectors.

A selector gates whether the v3.35 Strategy B
intervention should fire on a given trajectory. The
five selectors are the directive's named test set:

* ``NONE``             — baseline (always fire); this
  reproduces v3.35's non-specific behaviour.
* ``SUPPORT``          — fire only when the pre-audit
  ``support_state`` (index n-2) sits at the
  ``UNDER_AUDIT`` anchor (0.0).
* ``BRANCH_COST``      — fire only when the pre-audit
  ``branch_cost`` (index n-2) is at or above 2.0.
* ``FRAME_STABILITY``  — fire only when ``frame_id`` at
  index n-2 is at the directive's plateau-frame anchor
  (5.0). v3.38's separability map shows this is a
  perfect pre-audit separator on the mover universe.
* ``DUAL_TRIGGER``     — ``FRAME_STABILITY`` AND
  ``SUPPORT``: both pre-audit conditions must hold.

The predicates are pure functions of the trajectory's
state vectors; no class labels are read.
"""
from __future__ import annotations

from enum import Enum

from ..epistemic_trajectory.state import StateVector


# Anchors named by the directive's plateau geometry
# (v3.32 cause structure + v3.38 separability map).
_PLATEAU_FRAME_ID    = 5.0
_UNDER_AUDIT_ANCHOR  = 0.0
_BRANCH_COST_FLOOR   = 2.0


class SelectorKind(str, Enum):
    NONE            = "none"
    SUPPORT         = "support_condition"
    BRANCH_COST     = "branch_cost_condition"
    FRAME_STABILITY = "frame_stability_condition"
    DUAL_TRIGGER    = "dual_trigger_condition"


def _pre_audit(
    states: tuple[StateVector, ...],
) -> StateVector | None:
    if len(states) < 2:
        return None
    return states[-2]


def fires(
    selector: str, states: tuple[StateVector, ...],
) -> bool:
    pre = _pre_audit(states)
    if pre is None:
        return False
    if selector == SelectorKind.NONE.value:
        return True
    if selector == SelectorKind.SUPPORT.value:
        return pre.support_state == _UNDER_AUDIT_ANCHOR
    if selector == SelectorKind.BRANCH_COST.value:
        return pre.branch_cost >= _BRANCH_COST_FLOOR
    if selector == SelectorKind.FRAME_STABILITY.value:
        return pre.frame_id == _PLATEAU_FRAME_ID
    if selector == SelectorKind.DUAL_TRIGGER.value:
        return (
            pre.frame_id == _PLATEAU_FRAME_ID
            and pre.support_state == _UNDER_AUDIT_ANCHOR
        )
    return False


__all__ = [
    "SelectorKind", "fires",
]
