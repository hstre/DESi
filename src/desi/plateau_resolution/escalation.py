"""v3.33 — Strategy C and D.

* Strategy C: +2 extra audit stages. Append two
  pre-audit-anchor states to the trajectory and then
  simulate a re-audit. The simulation rule: if the
  highest confidence reached anywhere in the trajectory
  ≥ 0.5, the re-audit lands at LOGICALLY_SUPPORTED
  (4.0). Otherwise it stays at BRIDGE_REQUIRED (2.0).
* Strategy D: cause-specific escalation. The plateau's
  dominant cause is CONFIDENCE_OSCILLATION
  (v3.32 finding). The escalation aggressively boosts
  the final state's confidence to the trajectory's
  max-observed value, then simulates a re-audit by the
  same rule. If the boosted final confidence ≥ 0.5, the
  re-audit lands at SUPPORTED.

Both strategies operate on state vectors only - no
runtime rule changes, no actual auditor calls.
"""
from __future__ import annotations

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


_IDX_CONF      = DIMENSION_NAMES.index("confidence")
_IDX_SUPPORT   = DIMENSION_NAMES.index("support_state")
_REAUDIT_CONFIDENCE_FLOOR = 0.5
_SUPPORTED                = 4.0
_BRIDGE_REQUIRED          = 2.0


def _replace(s: StateVector, **u) -> StateVector:
    d = s.to_dict()
    d.update(u)
    return StateVector(**d)


def apply_extra_audit_stages(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Strategy C: append two pre-audit-anchor states
    plus a simulated re-audit final."""
    if len(states) < 2:
        return states
    anchor = states[-2]
    final_original = states[-1]
    max_conf = max(
        s.to_tuple()[_IDX_CONF] for s in states
    )
    if max_conf >= _REAUDIT_CONFIDENCE_FLOOR:
        new_support = _SUPPORTED
    else:
        new_support = _BRIDGE_REQUIRED
    new_final = _replace(
        final_original, support_state=new_support,
    )
    return (
        tuple(states[:-1]) + (anchor, anchor, new_final)
    )


def apply_cause_specific_escalation(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Strategy D: boost final state's confidence to the
    max observed value, then simulate re-audit."""
    if len(states) < 2:
        return states
    max_conf = max(
        s.to_tuple()[_IDX_CONF] for s in states
    )
    boosted_final = _replace(
        states[-1], confidence=max_conf,
    )
    if max_conf >= _REAUDIT_CONFIDENCE_FLOOR:
        boosted_final = _replace(
            boosted_final, support_state=_SUPPORTED,
        )
    return tuple(states[:-1]) + (boosted_final,)


__all__ = [
    "apply_cause_specific_escalation",
    "apply_extra_audit_stages",
]
