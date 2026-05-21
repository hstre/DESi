"""v27.3 - method trend drift over the ecology.

Thin views over the run: how many research lines stay present
and how plurality holds. Drift is bounded - nothing collapses to
zero - so research plurality is preserved.
"""
from __future__ import annotations

from .ecology import run


def min_active_ratio() -> float:
    return run().min_active_ratio


def plurality_preservation() -> float:
    """Fraction of research lines that remain present (non-zero
    strength) at the worst step, in [0, 1]. Nothing is deleted,
    so plurality does not collapse."""
    return run().min_active_ratio


def line_count() -> int:
    return run().method_count


__all__ = [
    "line_count",
    "min_active_ratio",
    "plurality_preservation",
]
