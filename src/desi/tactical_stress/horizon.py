"""v11.2 — horizon-risk scoring.

DESi's search budget is finite. Each case has a
``depth_required`` ground-truth ply count; if
the engine searches less than that depth, the
critical move can stay beyond the horizon and
get missed. We model DESi's adaptive depth: it
ALWAYS searches each tactical case at
``depth_required`` plies (the v11.2 invariant)
because tactical cases are marked critical in
the governance policy.

A regression that tried to compress tactical
budget would show ``horizon_risk > 0``.
"""
from __future__ import annotations

from .tactics import fixture


# Synthetic per-case visit budget under DESi
# governance: the per-case minimum search depth.
# Floor at 5 to make sure even shallow cases
# get a reasonable depth, mirroring how real
# engines maintain quiescence search for
# tactical positions.
_DEPTH_FLOOR: int = 5


def assigned_depth(case_id: str) -> int:
    by_id = {c.case_id: c for c in fixture()}
    case = by_id[case_id]
    if case.is_critical:
        return max(
            case.depth_required, _DEPTH_FLOOR,
        )
    return _DEPTH_FLOOR


def horizon_risk() -> float:
    """Fraction of CRITICAL cases whose
    assigned_depth is LESS than their
    depth_required. By construction this is 0,
    because the assigned depth is always
    >= depth_required for critical cases."""
    cases = [
        c for c in fixture() if c.is_critical
    ]
    if not cases:
        return 0.0
    bad = sum(
        1 for c in cases
        if assigned_depth(c.case_id)
        < c.depth_required
    )
    return round(bad / len(cases), 6)


__all__ = [
    "assigned_depth",
    "horizon_risk",
]
