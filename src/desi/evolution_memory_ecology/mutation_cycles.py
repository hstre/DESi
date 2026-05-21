"""v30.3 - mutation cycles across generations.

Observes the accept/reject rhythm across generations and the
recurrence of rejected (failed) versus accepted (successful)
evolution. Observation only.
"""
from __future__ import annotations

from .generations import run


def acceptance_series() -> tuple[int, ...]:
    return tuple(r.accepted for r in run().records)


def rejection_series() -> tuple[int, ...]:
    return tuple(r.rejected for r in run().records)


def generations_with_rejections() -> int:
    return sum(1 for r in run().records if r.rejected > 0)


def generations_with_acceptances() -> int:
    return sum(1 for r in run().records if r.accepted > 0)


def acceptance_ratio() -> float:
    r = run()
    if r.total_proposed == 0:
        return 0.0
    return round(r.total_accepted / r.total_proposed, 6)


__all__ = [
    "acceptance_ratio",
    "acceptance_series",
    "generations_with_acceptances",
    "generations_with_rejections",
    "rejection_series",
]
