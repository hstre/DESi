"""v6.3 — uncertainty / certainty-distribution
trajectories over the 500-step run."""
from __future__ import annotations

from collections import Counter

from ..adversarial_claims.conflict_injector import (
    CERTAINTY_LEVELS,
)
from .memory import (
    early_window, late_window,
)
from .world_drift import (
    STEP_COUNT, trajectory,
)


def _certainty_distribution(
    steps: tuple,
) -> dict[str, float]:
    cnt = Counter(s.certainty for s in steps)
    total = sum(cnt.values())
    if total == 0:
        return {
            k: 0.0 for k in CERTAINTY_LEVELS
        }
    return {
        k: cnt.get(k, 0) / total
        for k in CERTAINTY_LEVELS
    }


def early_distribution() -> dict[str, float]:
    return _certainty_distribution(
        early_window(trajectory()),
    )


def late_distribution() -> dict[str, float]:
    return _certainty_distribution(
        late_window(trajectory()),
    )


def high_certainty_rate() -> float:
    total = len(trajectory())
    if total == 0:
        return 0.0
    high = sum(
        1 for s in trajectory()
        if s.certainty == "high"
    )
    return round(high / total, 6)


def low_certainty_rate() -> float:
    total = len(trajectory())
    if total == 0:
        return 0.0
    low = sum(
        1 for s in trajectory()
        if s.certainty == "low"
    )
    return round(low / total, 6)


def total_variation_drift() -> float:
    """Total-variation distance between the
    early-window and late-window certainty
    distributions. 0 means stable, 1 means
    completely swapped."""
    e = early_distribution()
    l = late_distribution()
    tv = 0.5 * sum(
        abs(e[k] - l[k])
        for k in CERTAINTY_LEVELS
    )
    return round(tv, 6)


__all__ = [
    "early_distribution",
    "high_certainty_rate",
    "late_distribution",
    "low_certainty_rate",
    "total_variation_drift",
]
