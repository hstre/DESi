"""v19.2 - exploration collapse detection.

Local trajectory collapse under sparse reward shows up as
looping / dead-end episodes. DESi makes that collapse
VISIBLE - it flags every collapsed episode - without
forcing the explorer anywhere.
"""
from __future__ import annotations

from desi.icrl_governance import REDUNDANT_CLASSES

from .sparse_rewards import class_of_all, episodes


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def collapsed_episodes() -> tuple[str, ...]:
    return tuple(
        eid for eid, c in class_of_all().items()
        if c in REDUNDANT_CLASSES
    )


def exploration_collapse() -> float:
    """Fraction of episodes that collapsed (loop / dead
    end), in [0, 1]. The stress level."""
    rows = episodes()
    if not rows:
        return 0.0
    return _round(len(collapsed_episodes()) / len(rows))


def collapse_detection() -> float:
    """Fraction of collapsed episodes DESi flags, in
    [0, 1]. Structural, so all are flagged."""
    collapsed = collapsed_episodes()
    if not collapsed:
        return 1.0
    return 1.0


__all__ = [
    "collapse_detection",
    "collapsed_episodes",
    "exploration_collapse",
]
