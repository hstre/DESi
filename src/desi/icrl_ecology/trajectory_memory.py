"""v19.3 - trajectory memory and capture resistance.

Trajectory capture is when one trajectory family takes
over the whole exploration budget. Across the long run
DESi adopts no single trajectory family, so governed
capture stays at zero and exploration plurality holds.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def mean_capture() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.capture for s in states) / len(states)
    )


def trajectory_capture_resistance() -> float:
    """1 - mean governed trajectory capture, in [0, 1]."""
    return _round(1.0 - mean_capture())


def capture_occurred() -> bool:
    return any(s.capture > 0.05 for s in run())


def exploration_plurality() -> float:
    """Mean exploration plurality across the run, in
    [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.plurality for s in states) / len(states)
    )


def min_plurality() -> float:
    return _round(min(s.plurality for s in run()))


__all__ = [
    "capture_occurred",
    "exploration_plurality",
    "mean_capture",
    "min_plurality",
    "trajectory_capture_resistance",
]
