"""v19.1 - trajectory prioritisation.

Ranks trajectories by governed priority and reports the
budget share each receives, so it is auditable how DESi
shifts exploration effort toward informative paths
without removing any path.
"""
from __future__ import annotations

from .governance import (
    baseline_priorities, baseline_total, governed_priorities,
    governed_total,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governed_budget_share() -> dict[str, float]:
    total = governed_total()
    if total <= 0:
        return {k: 0.0 for k in governed_priorities()}
    return {
        k: _round(v / total)
        for k, v in governed_priorities().items()
    }


def baseline_budget_share() -> dict[str, float]:
    total = baseline_total()
    if total <= 0:
        return {k: 0.0 for k in baseline_priorities()}
    return {
        k: _round(v / total)
        for k, v in baseline_priorities().items()
    }


def ranked_trajectories() -> tuple[tuple[str, float], ...]:
    items = sorted(
        governed_priorities().items(),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return tuple(items)


__all__ = [
    "baseline_budget_share",
    "governed_budget_share",
    "ranked_trajectories",
]
