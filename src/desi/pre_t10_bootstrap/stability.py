"""v3.120b — stability summaries."""
from __future__ import annotations

import statistics

from .bootstrap import all_bootstrap_draws


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def threshold_mean() -> float:
    draws = [
        d.threshold
        for d in all_bootstrap_draws()
        if d.threshold >= 0
    ]
    if not draws:
        return -1.0
    return _round(sum(draws) / len(draws))


def threshold_ci() -> tuple[float, float]:
    """5th and 95th percentile of the
    bootstrap threshold distribution. Returns
    (-1.0, -1.0) when no valid draws."""
    draws = sorted(
        d.threshold
        for d in all_bootstrap_draws()
        if d.threshold >= 0
    )
    if not draws:
        return (-1.0, -1.0)
    n = len(draws)
    lo = draws[max(0, int(0.05 * n))]
    hi = draws[
        min(n - 1, int(0.95 * n))
    ]
    return (_round(lo), _round(hi))


def threshold_drift() -> float:
    """Max absolute deviation from the
    reference v3.119 threshold (0.542)."""
    ref = 0.541667
    draws = [
        d.threshold
        for d in all_bootstrap_draws()
        if d.threshold >= 0
    ]
    if not draws:
        return 1.0
    return _round(max(abs(t - ref) for t in draws))


def seed_invariance() -> float:
    """Fraction of bootstrap draws whose
    threshold matches the modal threshold."""
    draws = [
        d.threshold
        for d in all_bootstrap_draws()
        if d.threshold >= 0
    ]
    if not draws:
        return 0.0
    from collections import Counter
    cnt = Counter(draws)
    most_common = cnt.most_common(1)[0][1]
    return _round(most_common / len(draws))


__all__ = [
    "seed_invariance",
    "threshold_ci",
    "threshold_drift",
    "threshold_mean",
]
