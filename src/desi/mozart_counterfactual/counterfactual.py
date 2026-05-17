"""v3.70 — counterfactual aggregation helpers.

Wraps the swap harness with summary accessors used by
the report.
"""
from __future__ import annotations

from ..mozart_probe.coverage import probe_coverage
from .swap import (
    SwapResult, all_swap_results,
    input_specificity,
)


def mozart_baseline_score() -> float:
    return probe_coverage(
        "sample:n03_mozart",
    ).coverage_score


def aggregate() -> tuple[
    tuple[SwapResult, ...], float, float,
]:
    swaps = all_swap_results()
    mozart_score = mozart_baseline_score()
    spec = input_specificity(swaps, mozart_score)
    return swaps, mozart_score, spec


__all__ = [
    "aggregate", "mozart_baseline_score",
]
