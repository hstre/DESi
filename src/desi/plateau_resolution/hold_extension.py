"""v3.33 — Strategy B: +1 extra confidence_hold.

Apply an additional confidence_hold action one step
earlier than the v3.30 cause-aware controller would. By
clamping confidence at n-3 instead of n-2, the audit
step inherits a more anchored confidence value. The
strategy then withdraws the audit step (same as v3.30
cause-aware actions) so the final state moves from
BRIDGE_REQUIRED (2.0) to UNDER_AUDIT (0.0).
"""
from __future__ import annotations

from ..cause_aware_control.actions import (
    _confidence_hold_with_withdraw,  # noqa: WPS437
)
from ..epistemic_trajectory.state import StateVector


def apply_extra_confidence_hold(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """Apply confidence_hold at index ``max(0, n-3)``,
    one step earlier than the v3.30 controller's
    intervention point."""
    n = len(states)
    if n < 3:
        return states
    return _confidence_hold_with_withdraw(states, n - 3)


__all__ = ["apply_extra_confidence_hold"]
