"""v3.120a — derive optimum and feasibility
window from the sweep."""
from __future__ import annotations

from .threshold import all_sweep_cells


_FAR_CEILING: float = 0.10
_TPR_FLOOR: float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def feasible_cells() -> tuple:
    return tuple(
        c for c in all_sweep_cells()
        if c.far <= _FAR_CEILING
        and c.tpr >= _TPR_FLOOR
    )


def threshold_window() -> tuple[float, float]:
    feas = feasible_cells()
    if not feas:
        return (-1.0, -1.0)
    ts = sorted(c.threshold for c in feas)
    return (ts[0], ts[-1])


def window_width() -> float:
    lo, hi = threshold_window()
    if lo < 0.0:
        return 0.0
    return _round(hi - lo)


def optimal_threshold() -> float:
    """Threshold that minimises FAR while keeping
    TPR == 1.0. If no such threshold exists in
    the sweep, return the threshold with the
    BEST joint score (TPR primary, then -FAR)
    among TPR == 1.0 cells."""
    cells = all_sweep_cells()
    tpr_full = [c for c in cells if c.tpr >= _TPR_FLOOR]
    if not tpr_full:
        return -1.0
    return min(
        tpr_full,
        key=lambda c: (c.far, c.threshold),
    ).threshold


def best_far_at_full_tpr() -> float:
    cells = all_sweep_cells()
    tpr_full = [c for c in cells if c.tpr >= _TPR_FLOOR]
    if not tpr_full:
        return 1.0
    return min(c.far for c in tpr_full)


def best_tpr_at_zero_far() -> float:
    cells = all_sweep_cells()
    zero_far = [c for c in cells if c.far == 0.0]
    if not zero_far:
        return 0.0
    return max(c.tpr for c in zero_far)


__all__ = [
    "best_far_at_full_tpr",
    "best_tpr_at_zero_far",
    "feasible_cells",
    "optimal_threshold",
    "threshold_window",
    "window_width",
]
