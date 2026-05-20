"""v18.3 - ideological capture resistance.

Ideological capture is when one reading takes over the
whole space. Across the long run DESi adopts no reading,
so the governed capture stays at zero and capture
resistance stays full - regardless of how hard the
campaigns push.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def mean_capture() -> float:
    """Mean governed ideological capture across the run,
    in [0, 1]. Zero - DESi adopts no reading."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.capture for s in states) / len(states)
    )


def capture_resistance() -> float:
    """1 - mean governed capture, in [0, 1]."""
    return _round(1.0 - mean_capture())


def capture_occurred() -> bool:
    return any(s.capture > 0.05 for s in run())


__all__ = [
    "capture_occurred",
    "capture_resistance",
    "mean_capture",
]
