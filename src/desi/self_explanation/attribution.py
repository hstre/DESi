"""v3.37 — decisive-dimension attribution.

Given per-dimension deltas, identify:

* ``first_changed_dimension`` — the dimension that
  changed at the lowest index (ties broken by
  DIMENSION_NAMES order, which is the directive's fixed
  ordering).
* ``decisive_dimension`` — the dimension whose
  restoration to the original at the final state would
  revert the verdict. The verdict is determined by
  ``support_state`` of the final state, so this is a
  closed-form lookup (no leave-one-out re-audit).

If no delta touches the final state, the verdict cannot
have changed and the case is flagged ``unexplained``.
"""
from __future__ import annotations

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from .counterfactual import DimensionDelta


def first_changed_dimension(
    deltas: tuple[DimensionDelta, ...],
) -> str | None:
    """The dimension changed at the smallest index.
    Stable tie-break: DIMENSION_NAMES order."""
    if not deltas:
        return None
    min_idx = min(d.index for d in deltas)
    head = [d for d in deltas if d.index == min_idx]
    order = {n: i for i, n in enumerate(DIMENSION_NAMES)}
    head.sort(key=lambda d: order[d.dimension])
    return head[0].dimension


def decisive_dimension(
    original: tuple[StateVector, ...],
    counterfactual: tuple[StateVector, ...],
    deltas: tuple[DimensionDelta, ...],
) -> str | None:
    """The dimension whose restoration at the final
    state reverts the verdict. Returns ``None`` when no
    final-state delta is present (i.e. the verdict
    could not have changed and the case is
    unexplained)."""
    if not original or not counterfactual:
        return None
    final_idx = len(counterfactual) - 1
    orig_v = original[final_idx].support_state
    cf_v = counterfactual[final_idx].support_state
    if orig_v == cf_v:
        return None  # no verdict change
    final_deltas = [
        d for d in deltas if d.index == final_idx
    ]
    if not final_deltas:
        return None  # cannot localise
    # The verdict IS support_state; if support_state is
    # among the final-index deltas it is by definition
    # decisive. Otherwise fall back to the largest
    # magnitude at the final index.
    for d in final_deltas:
        if d.dimension == "support_state":
            return "support_state"
    return max(
        final_deltas, key=lambda d: d.magnitude,
    ).dimension


def confidence_hold_was_noop(
    deltas: tuple[DimensionDelta, ...],
    audit_index: int,
) -> bool:
    """True when no delta touches ``confidence`` at any
    index other than the final state. (The audit-step
    withdrawal acts on ``support_state`` only, so any
    confidence delta would be evidence of the
    confidence_hold component doing work.)"""
    for d in deltas:
        if d.dimension == "confidence" and d.index != audit_index:
            return False
        if d.dimension == "confidence":
            # confidence change at the final index is
            # still confidence_hold work (clamps the
            # decaying tail).
            return False
    return True


__all__ = [
    "confidence_hold_was_noop", "decisive_dimension",
    "first_changed_dimension",
]
