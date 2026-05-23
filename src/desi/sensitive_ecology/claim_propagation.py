"""v17.3 - claim propagation and source-quality
visibility.

However many leaks, manipulated files, and viral
waves wash through the ecology, DESi keeps the
quality of each source LABELLED and visible. A reader
can always see whether a propagated claim rests on a
chain-of-custody record or an anonymous repost.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def source_quality_visibility() -> float:
    """Mean fraction of source quality kept visible
    across the run, in [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.source_quality_visibility for s in states)
        / len(states)
    )


def min_source_quality_visibility() -> float:
    return _round(
        min(s.source_quality_visibility for s in run())
    )


def source_quality_always_visible() -> bool:
    """Source quality never falls below a high floor,
    even under maximal contamination."""
    return min_source_quality_visibility() >= 0.90


__all__ = [
    "min_source_quality_visibility",
    "source_quality_always_visible",
    "source_quality_visibility",
]
