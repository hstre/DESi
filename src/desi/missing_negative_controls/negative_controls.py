"""v3.77 — negative control aggregation.

Wraps the null-space harness with summary metrics
matching the directive.
"""
from __future__ import annotations

from .null_space import (
    NullControlOutcome,
    all_null_control_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def total_perturbations(
    outcomes: tuple[NullControlOutcome, ...],
) -> int:
    return len(outcomes)


def total_false_missing(
    outcomes: tuple[NullControlOutcome, ...],
) -> int:
    return sum(
        1 for o in outcomes
        if o.false_missing_claims > 0
    )


def false_missing_claim_rate(
    outcomes: tuple[NullControlOutcome, ...],
) -> float:
    if not outcomes:
        return 0.0
    return _round(
        total_false_missing(outcomes) / len(outcomes),
    )


def noise_rejection_rate(
    outcomes: tuple[NullControlOutcome, ...],
) -> float:
    if not outcomes:
        return 0.0
    rejected = sum(
        1 for o in outcomes
        if o.false_missing_claims == 0
    )
    return _round(rejected / len(outcomes))


def null_stability() -> float:
    a = [
        o.to_dict()
        for o in all_null_control_outcomes()
    ]
    b = [
        o.to_dict()
        for o in all_null_control_outcomes()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


__all__ = [
    "false_missing_claim_rate",
    "noise_rejection_rate", "null_stability",
    "total_false_missing", "total_perturbations",
]
