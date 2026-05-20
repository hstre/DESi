"""v19.0 - search redundancy and loop detection.

Measures how much of the exploration is redundant
revisiting and flags repetitive policy loops. DESi
MARKS these; it never deletes a trajectory or forces
the policy away from them.
"""
from __future__ import annotations

from .claims import ExplorationClass, REDUNDANT_CLASSES
from .trajectories import (
    class_of_all, exploration_class, trajectories,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trajectory_redundancy() -> float:
    """Mean internal redundancy across the corpus, in
    [0, 1]."""
    rows = trajectories()
    if not rows:
        return 0.0
    return _round(
        sum(t.internal_redundancy() for t in rows)
        / len(rows)
    )


def looping_trajectories() -> tuple[str, ...]:
    return tuple(
        tid for tid, c in class_of_all().items()
        if c == ExplorationClass.LOOPING.value
    )


def redundant_trajectories() -> tuple[str, ...]:
    return tuple(
        tid for tid, c in class_of_all().items()
        if c in REDUNDANT_CLASSES
    )


def loop_detection() -> float:
    """Fraction of looping trajectories DESi flags, in
    [0, 1]. Structural detection, so all are flagged."""
    loops = looping_trajectories()
    if not loops:
        return 1.0
    flagged = sum(
        1 for tid in loops
        if exploration_class(tid)
        == ExplorationClass.LOOPING.value
    )
    return _round(flagged / len(loops))


def redundant_fraction() -> float:
    """Fraction of trajectories in a redundant class, in
    [0, 1]."""
    rows = trajectories()
    if not rows:
        return 0.0
    return _round(len(redundant_trajectories()) / len(rows))


__all__ = [
    "loop_detection",
    "looping_trajectories",
    "redundant_fraction",
    "redundant_trajectories",
    "trajectory_redundancy",
]
