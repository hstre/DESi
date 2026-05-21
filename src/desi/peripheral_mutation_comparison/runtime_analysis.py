"""v31.2 - measured runtime analysis.

Reads the real recompute counts from the v31.1 mutation engine
and reports the measured runtime delta. Deterministic; cached so
the real mutations execute once.
"""
from __future__ import annotations

from functools import lru_cache

from desi.peripheral_mutation_real import (
    runtime_reduction, total_baseline_recomputes,
    total_mutated_recomputes,
)


@lru_cache(maxsize=1)
def baseline_recomputes() -> int:
    return total_baseline_recomputes()


@lru_cache(maxsize=1)
def mutated_recomputes() -> int:
    return total_mutated_recomputes()


@lru_cache(maxsize=1)
def measured_improvement() -> float:
    """The measured recompute reduction of the mutated version
    versus the baseline, in [0, 1]."""
    return runtime_reduction()


__all__ = [
    "baseline_recomputes",
    "measured_improvement",
    "mutated_recomputes",
]
