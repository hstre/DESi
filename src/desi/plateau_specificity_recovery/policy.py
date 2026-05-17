"""v3.39 — gated intervention policy.

Composition: selector + Strategy B (apply_k_holds with
k=1). If the selector fires on a trajectory the
intervention is applied; otherwise the original
states are returned unchanged.
"""
from __future__ import annotations

from ..epistemic_trajectory.state import StateVector
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from .selector import fires


def apply_policy(
    states: tuple[StateVector, ...], selector: str,
) -> tuple[StateVector, ...]:
    if not fires(selector, states):
        return states
    return apply_k_holds(states, 1)


__all__ = ["apply_policy"]
