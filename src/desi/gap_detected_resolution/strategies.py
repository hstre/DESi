"""v3.48 — closed-set GAP resolution strategies.

Seven strategies, each a pure function on the original
state tuple. No re-audit, no rule changes — every
strategy only re-shapes the final state vector (or
the audit-step anchor) of the same trajectory.

* ``A_NO_CHANGE``               — identity baseline
* ``B_CONFIDENCE_HOLD``         — v3.33 Strategy B
  (apply_k_holds with k=1: confidence_hold at n-3 +
  audit-step withdrawal to states[-2].support_state)
* ``C_AUDIT_DELAY``             — anchor the audit on
  states[-3] instead of states[-2]: a deferred
  audit-step withdrawal that ignores the most recent
  audit and re-anchors one step earlier
* ``D_BRIDGE_EXPANSION``        — escalate the
  GAP_DETECTED final (1.0) to BRIDGE_REQUIRED (2.0);
  only fires on trajectories whose final state is at
  GAP_DETECTED so it cannot overcontrol healthy
  trajectories
* ``E_PREMISE_REEXTRACTION``    — bump the final
  state's anchor_density by 5x as a stand-in for
  re-extracting premises with more anchors. Final
  support_state is unchanged, so this strategy never
  resolves a GAP but never overcontrols either
* ``F_FRAME_REPLAY``            — v3.30 frame_replay
  cause-action applied at index n-3 (clamps frame_id
  + withdraws audit step)
* ``G_BRIDGE_AND_PREMISE``      — D ∘ E: escalate to
  BRIDGE_REQUIRED AND bump anchor_density; gated on
  final state == GAP_DETECTED for D's behaviour.
"""
from __future__ import annotations

from enum import Enum

from ..cause_aware_control.actions import (
    apply_frame_replay,
)
from ..epistemic_trajectory.state import StateVector
from ..gap_detected.state import GAP_DETECTED_STATE
from ..plateau_hold_sweep.hold_sweep import apply_k_holds


_BRIDGE_REQUIRED_STATE = 2.0
_PREMISE_BUMP_FACTOR   = 5.0


class StrategyKind(str, Enum):
    A_NO_CHANGE           = "A_no_change"
    B_CONFIDENCE_HOLD     = "B_confidence_hold"
    C_AUDIT_DELAY         = "C_audit_delay"
    D_BRIDGE_EXPANSION    = "D_bridge_expansion"
    E_PREMISE_REEXTRACT   = "E_premise_re_extraction"
    F_FRAME_REPLAY        = "F_frame_replay"
    G_BRIDGE_AND_PREMISE  = "G_bridge_and_premise"


def _replace(s: StateVector, **u) -> StateVector:
    d = s.to_dict()
    d.update(u)
    return StateVector(**d)


def strategy_a(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    return states


def strategy_b(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    return apply_k_holds(states, 1)


def strategy_c(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Audit delay — re-anchor on states[-3] instead
    of states[-2]. The final's support is replaced by
    the n-3 audit-step anchor."""
    if len(states) < 3:
        return states
    anchor = states[-3].support_state
    return tuple(states[:-1]) + (
        _replace(states[-1], support_state=anchor),
    )


def strategy_d(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Bridge expansion — gated on final == GAP."""
    if not states:
        return states
    if states[-1].support_state != GAP_DETECTED_STATE:
        return states
    return tuple(states[:-1]) + (
        _replace(
            states[-1],
            support_state=_BRIDGE_REQUIRED_STATE,
        ),
    )


def strategy_e(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Premise re-extraction — bump anchor_density by
    5x at the final state. Support state is unchanged."""
    if not states:
        return states
    new = states[-1].anchor_density * _PREMISE_BUMP_FACTOR
    return tuple(states[:-1]) + (
        _replace(states[-1], anchor_density=new),
    )


def strategy_f(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    if len(states) < 3:
        return states
    return apply_frame_replay(states, len(states) - 3)


def strategy_g(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Bridge expansion AND premise re-extraction."""
    return strategy_e(strategy_d(states))


_DISPATCH = {
    StrategyKind.A_NO_CHANGE.value:           strategy_a,
    StrategyKind.B_CONFIDENCE_HOLD.value:     strategy_b,
    StrategyKind.C_AUDIT_DELAY.value:         strategy_c,
    StrategyKind.D_BRIDGE_EXPANSION.value:    strategy_d,
    StrategyKind.E_PREMISE_REEXTRACT.value:   strategy_e,
    StrategyKind.F_FRAME_REPLAY.value:        strategy_f,
    StrategyKind.G_BRIDGE_AND_PREMISE.value:  strategy_g,
}


def apply_strategy(
    states: tuple[StateVector, ...], strategy: str,
) -> tuple[StateVector, ...]:
    fn = _DISPATCH.get(strategy)
    if fn is None:
        return states
    return fn(states)


__all__ = [
    "StrategyKind", "apply_strategy", "strategy_a",
    "strategy_b", "strategy_c", "strategy_d",
    "strategy_e", "strategy_f", "strategy_g",
]
