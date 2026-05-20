"""v18.3 - plurality preservation over the long horizon.

However many schisms, missionary waves, and debunking
campaigns pass through, DESi keeps plurality high and
alternative readings visible. This module measures that
plurality does NOT decay.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def plurality_preservation() -> float:
    """Mean plurality across the run, in [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.plurality for s in states) / len(states)
    )


def min_plurality() -> float:
    return _round(min(s.plurality for s in run()))


def alternative_visibility() -> float:
    """Mean visibility of alternative readings across the
    run, in [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.alternative_visibility for s in states)
        / len(states)
    )


def plurality_collapsed() -> bool:
    return min_plurality() < 0.90


__all__ = [
    "alternative_visibility",
    "min_plurality",
    "plurality_collapsed",
    "plurality_preservation",
]
