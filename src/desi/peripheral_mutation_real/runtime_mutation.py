"""v31.1 - runtime mutation view.

Aggregates the runtime effect of the real mutations as a measured
recompute reduction across all successful mutations.
"""
from __future__ import annotations

from .mutation_engine import real_mutations, successful_mutations


def total_baseline_recomputes() -> int:
    return sum(m.baseline_recomputes for m in real_mutations())


def total_mutated_recomputes() -> int:
    return sum(m.mutated_recomputes for m in real_mutations())


def runtime_reduction() -> float:
    """Aggregate measured recompute reduction, in [0, 1]."""
    base = total_baseline_recomputes()
    if base == 0:
        return 0.0
    return round(
        (base - total_mutated_recomputes()) / base, 6,
    )


def successful_mutation_rate() -> float:
    ms = real_mutations()
    if not ms:
        return 0.0
    return round(len(successful_mutations()) / len(ms), 6)


__all__ = [
    "runtime_reduction",
    "successful_mutation_rate",
    "total_baseline_recomputes",
    "total_mutated_recomputes",
]
