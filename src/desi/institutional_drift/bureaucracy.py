"""v10.3 — bureaucracy-growth / flexibility-
loss metrics over the trajectory."""
from __future__ import annotations

from .institutional_drift import trajectory


SHORT_WINDOW: int = 1000


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean_quality(steps: tuple) -> float:
    if not steps:
        return 0.0
    return sum(
        s.quality_score for s in steps
    ) / len(steps)


def bureaucracy_growth() -> float:
    """If the mean quality_score systematically
    DROPS between the early and late window,
    that's a sign of bureaucracy taking over -
    decisions become rote / mis-aligned rather
    than substantive. The metric is the
    early-minus-late drop, clipped at 0."""
    early = _mean_quality(
        trajectory()[:SHORT_WINDOW],
    )
    late = _mean_quality(
        trajectory()[-SHORT_WINDOW:],
    )
    return _round(max(0.0, early - late))


def flexibility_loss() -> float:
    """Same shape as bureaucracy_growth but
    measured on a separate axis: do the closed-
    enum hashes shrink the set of distinct
    quality_scores over time? If quality
    collapses to a single value in the late
    window, the institution has lost
    flexibility."""
    early = trajectory()[:SHORT_WINDOW]
    late = trajectory()[-SHORT_WINDOW:]
    e_unique = len({
        s.quality_score for s in early
    })
    l_unique = len({
        s.quality_score for s in late
    })
    if e_unique == 0:
        return 0.0
    drop = max(0, e_unique - l_unique)
    return _round(drop / e_unique)


__all__ = [
    "SHORT_WINDOW",
    "bureaucracy_growth",
    "flexibility_loss",
]
