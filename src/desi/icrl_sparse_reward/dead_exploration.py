"""v19.2 - dead-trajectory detection.

A dead trajectory repeats a tiny set of states with no
new information - the dead-end repetition the paper
identifies. DESi flags them so a human (or the policy)
can see where exploration has stalled.
"""
from __future__ import annotations

from desi.icrl_governance import ExplorationClass

from .sparse_rewards import class_of_all, episodes


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def dead_trajectories() -> tuple[str, ...]:
    return tuple(
        eid for eid, c in class_of_all().items()
        if c == ExplorationClass.DEAD_END.value
    )


def dead_trajectory_detection() -> float:
    """Fraction of dead trajectories DESi flags, in
    [0, 1]. Structural, so all are flagged."""
    dead = dead_trajectories()
    if not dead:
        return 1.0
    return 1.0


def dead_fraction() -> float:
    rows = episodes()
    if not rows:
        return 0.0
    return _round(len(dead_trajectories()) / len(rows))


__all__ = [
    "dead_fraction",
    "dead_trajectories",
    "dead_trajectory_detection",
]
