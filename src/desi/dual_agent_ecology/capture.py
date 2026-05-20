"""v20.3 - governance capture resistance.

Governance capture is when one agent (the wild OR DESi
itself) takes over the joint process. Across the long run
DESi keeps the capture at zero, so the dual-agent balance
holds: the wild stays productive and DESi stays a governor,
not an authority.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def mean_capture() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(sum(s.capture for s in states) / len(states))


def capture_resistance() -> float:
    """1 - mean governance capture, in [0, 1]."""
    return _round(1.0 - mean_capture())


def capture_occurred() -> bool:
    return any(s.capture > 0.05 for s in run())


__all__ = [
    "capture_occurred",
    "capture_resistance",
    "mean_capture",
]
