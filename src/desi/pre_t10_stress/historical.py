"""v3.120c — stress aggregates."""
from __future__ import annotations

from .stress import all_stress_cells


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def historical_tpr_min() -> float:
    cells = all_stress_cells()
    if not cells:
        return 0.0
    return _round(min(c.tpr for c in cells))


def historical_tpr_max() -> float:
    cells = all_stress_cells()
    if not cells:
        return 0.0
    return _round(max(c.tpr for c in cells))


def false_negative_rate_max() -> float:
    """Highest FNR observed across stress cells.
    FNR = 1 - TPR."""
    return _round(1.0 - historical_tpr_min())


def adverse_flip_count() -> int:
    """Cells where TPR drops below 1.0 are
    counted as adverse flips of the rule's
    recall guarantee."""
    cells = all_stress_cells()
    return sum(
        1 for c in cells if c.tpr < 1.0
    )


def cell_count() -> int:
    return len(all_stress_cells())


__all__ = [
    "adverse_flip_count",
    "cell_count",
    "false_negative_rate_max",
    "historical_tpr_max",
    "historical_tpr_min",
]
