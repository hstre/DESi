"""v3.64 — causal-importance ranking.

Wraps the ablation harness with summary helpers used
by the report.
"""
from __future__ import annotations

from .ablation import (
    AblationResult, necessary_factors, run_ablations,
    sufficient_factors,
)


def rank_by_importance(
    results: tuple[AblationResult, ...],
) -> tuple[AblationResult, ...]:
    """Sort ablation results by causal_importance
    descending. Low-power subsets are pushed to the
    end of their importance band."""
    return tuple(
        sorted(
            results,
            key=lambda r: (
                -r.causal_importance,
                r.low_power,
                r.factor,
            ),
        )
    )


def aggregate() -> tuple[
    tuple[AblationResult, ...],
    tuple[str, ...], tuple[str, ...],
]:
    results = run_ablations()
    return (
        results, necessary_factors(results),
        sufficient_factors(results),
    )


__all__ = [
    "aggregate", "rank_by_importance",
]
