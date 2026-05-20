"""v16.3 - narrative inflation and mythologization
growth.

Both quantities genuinely grow over the decades -
that is the historical reality DESi must make
visible. The point is that under DESi's hygiene
they grow in a BOUNDED, saturating way and never
displace the verified core.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def narrative_inflation() -> float:
    """Governed narrative inflation at the end of
    the run, in [0, 1]. Bounded by DESi's hygiene
    cap."""
    states = run()
    if not states:
        return 0.0
    return states[-1].narrative_inflation


def narrative_inflation_bounded() -> bool:
    """Inflation must be monotone non-decreasing and
    stay below the hygiene cap - growth is visible
    but never runaway."""
    states = run()
    vals = [s.narrative_inflation for s in states]
    monotone = all(
        vals[i] <= vals[i + 1] + 1e-9
        for i in range(len(vals) - 1)
    )
    return monotone and vals[-1] <= 0.25


def mythologization_growth() -> float:
    """Growth in secondary myth level from the start
    to the end of the run, in [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        states[-1].mythologization
        - states[0].mythologization
    )


def drift_visible() -> bool:
    """Drift is visible iff the run records a moving
    state (inflation actually changes over time)."""
    states = run()
    if len(states) < 2:
        return False
    return (
        states[-1].narrative_inflation
        > states[0].narrative_inflation
    )


__all__ = [
    "drift_visible",
    "mythologization_growth",
    "narrative_inflation",
    "narrative_inflation_bounded",
]
