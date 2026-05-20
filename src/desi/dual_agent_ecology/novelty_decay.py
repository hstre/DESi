"""v20.3 - novelty visibility under exhaustion.

Novelty exhausts over a long run. DESi keeps it VISIBLE:
the visibility floor stays high, so informative exploration
is never buried by hallucination growth or governance
fatigue.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def novelty_visibility() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.novelty_visibility for s in states) / len(states)
    )


def min_novelty_visibility() -> float:
    return _round(min(s.novelty_visibility for s in run()))


def novelty_stays_visible() -> bool:
    return min_novelty_visibility() >= 0.90


__all__ = [
    "min_novelty_visibility",
    "novelty_stays_visible",
    "novelty_visibility",
]
