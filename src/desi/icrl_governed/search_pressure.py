"""v19.1 - search pressure and redundancy reduction.

Quantifies how much exploration effort the baseline RL
explorer spends on redundant search vs how much DESi's
governance lets through. The reduction is the slack DESi
recovers - achieved by RE-WEIGHTING, never by deleting a
path.
"""
from __future__ import annotations

from desi.icrl_governance import REDUNDANT_CLASSES, class_of_all

from .governance import baseline_priorities, governed_priorities


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _redundant_ids() -> tuple[str, ...]:
    return tuple(
        tid for tid, c in class_of_all().items()
        if c in REDUNDANT_CLASSES
    )


def baseline_redundant_weight() -> float:
    base = baseline_priorities()
    return _round(sum(base[t] for t in _redundant_ids()))


def governed_redundant_weight() -> float:
    gov = governed_priorities()
    return _round(sum(gov[t] for t in _redundant_ids()))


def redundancy_reduction() -> float:
    """1 - (governed redundant weight / baseline redundant
    weight), in [0, 1]. How much redundant search effort
    DESi reweights away."""
    base = baseline_redundant_weight()
    if base <= 0:
        return 0.0
    return _round(
        1.0 - governed_redundant_weight() / base
    )


def search_pressure_relief() -> float:
    """1 - (governed total budget / baseline total budget):
    the overall shrink of the effective search effort."""
    from .governance import baseline_total, governed_total
    base = baseline_total()
    if base <= 0:
        return 0.0
    return _round(1.0 - governed_total() / base)


__all__ = [
    "baseline_redundant_weight",
    "governed_redundant_weight",
    "redundancy_reduction",
    "search_pressure_relief",
]
