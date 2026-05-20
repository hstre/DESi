"""v3.30 — cause-specific actions.

Closed set, one action per non-UNKNOWN cause class plus
UNKNOWN → rollback.

* ``support_hold``    — clamp support_state at its
  pre-audit value at every later state. Targets
  SUPPORT_DECAY.
* ``frame_replay``    — re-issue frame_id at every later
  state from the pre-collision value. Targets
  FRAME_COLLISION.
* ``branch_prune``    — clamp branch_cost at a
  reduced ceiling. Targets BRANCH_OVERLOAD.
* ``causal_suspend``  — clamp novelty at every later
  state to its pre-leap value. Targets CAUSAL_LEAP.
* ``confidence_hold`` — inherited from v3.26. Targets
  CONFIDENCE_OSCILLATION.
* ``rollback_last_transition`` — inherited from v3.27.
  Used only when the cause is UNKNOWN.

No rule changes, no frame overrides at the runtime
layer, no causal overrides. Each action only re-shapes
existing state vectors of the existing trajectory.
"""
from __future__ import annotations

from enum import Enum

from ..epistemic_trajectory.state import StateVector
from ..trajectory_control.actions import (
    apply_confidence_hold,
)
from ..trajectory_control.rollback import (
    apply_rollback_last_transition,
)


class CauseActionKind(str, Enum):
    SUPPORT_HOLD              = "support_hold"
    FRAME_REPLAY              = "frame_replay"
    BRANCH_PRUNE              = "branch_prune"
    CAUSAL_SUSPEND            = "causal_suspend"
    CONFIDENCE_HOLD           = "confidence_hold"
    ROLLBACK_LAST_TRANSITION  = "rollback_last_transition"


def _replace(s: StateVector, **updates) -> StateVector:
    d = s.to_dict()
    d.update(updates)
    return StateVector(**d)


# Every cause-action is a *cause-aware withdraw*: it
# clamps the cause-relevant dimension AND forces the
# audit-step support_state back to its pre-audit anchor
# (UNDER_AUDIT). This models "we intervened upstream and
# the audit did not commit". The behavioural rescue is
# identical to rollback; the cause-aware aspect lies in
# (a) which dimension carries the clamp side-effect and
# (b) which trajectories are eligible for the action.


def _withdraw_audit_step(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Replace the final state's support_state with the
    pre-audit anchor."""
    if len(states) < 2:
        return states
    anchor = states[-2].support_state
    final = _replace(states[-1], support_state=anchor)
    return tuple(states[:-1]) + (final,)


def apply_support_hold(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Maintain support_state at the pre-audit anchor
    for every later state. Targets SUPPORT_DECAY."""
    if at <= 0 or at >= len(states):
        return states
    anchor = states[at - 1].support_state
    out = list(states[: at])
    for s in states[at:]:
        out.append(_replace(s, support_state=anchor))
    return _withdraw_audit_step(tuple(out))


def apply_frame_replay(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Restore frame_id from the pre-collision anchor at
    every later state. Targets FRAME_COLLISION."""
    if at <= 0 or at >= len(states):
        return states
    anchor = states[at - 1].frame_id
    out = list(states[: at])
    for s in states[at:]:
        out.append(_replace(s, frame_id=anchor))
    return _withdraw_audit_step(tuple(out))


def apply_branch_prune(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Clamp branch_cost at every state from ``at``
    onwards to at most half the pre-warning value.
    Targets BRANCH_OVERLOAD."""
    if at <= 0 or at >= len(states):
        return states
    cap = max(1.0, states[at - 1].branch_cost / 2.0)
    out = list(states[: at])
    for s in states[at:]:
        new_branch = min(s.branch_cost, cap)
        out.append(_replace(s, branch_cost=new_branch))
    return _withdraw_audit_step(tuple(out))


def apply_causal_suspend(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Clamp novelty at every state from ``at`` onwards
    to its pre-leap value. Targets CAUSAL_LEAP."""
    if at <= 0 or at >= len(states):
        return states
    anchor = states[at - 1].novelty
    out = list(states[: at])
    for s in states[at:]:
        new_nov = min(s.novelty, anchor)
        out.append(_replace(s, novelty=new_nov))
    return _withdraw_audit_step(tuple(out))


def _confidence_hold_with_withdraw(
    states: tuple[StateVector, ...], at: int,
) -> tuple[StateVector, ...]:
    """Inherit the v3.26 confidence_hold semantics but
    also withdraw the audit step (so the rescue effect
    matches the other cause-aware actions)."""
    after_hold = apply_confidence_hold(states, at)
    return _withdraw_audit_step(after_hold)


_DISPATCH = {
    CauseActionKind.SUPPORT_HOLD.value:
        apply_support_hold,
    CauseActionKind.FRAME_REPLAY.value:
        apply_frame_replay,
    CauseActionKind.BRANCH_PRUNE.value:
        apply_branch_prune,
    CauseActionKind.CAUSAL_SUSPEND.value:
        apply_causal_suspend,
    CauseActionKind.CONFIDENCE_HOLD.value:
        _confidence_hold_with_withdraw,
    CauseActionKind.ROLLBACK_LAST_TRANSITION.value:
        apply_rollback_last_transition,
}


def apply_cause_action(
    states: tuple[StateVector, ...], action: str, at: int,
) -> tuple[StateVector, ...]:
    fn = _DISPATCH.get(action)
    if fn is None:
        return states
    return fn(states, at)


__all__ = [
    "CauseActionKind", "apply_branch_prune",
    "apply_causal_suspend", "apply_cause_action",
    "apply_frame_replay", "apply_support_hold",
]
