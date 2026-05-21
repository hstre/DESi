"""v33.0 - the immutable benchmark/core boundary.

The whole point of the benchmark compatibility layer is that
benchmarks may TEST DESi but may never STEER it. This module pins
the operations a benchmark task is forbidden from triggering - any
change to the protected epistemic core - and the small set of
adapter-layer operations that are allowed. The protected core set is
imported from the v31 boundary layer; it is NOT redefined here, so
the benchmark API cannot widen or weaken it.
"""
from __future__ import annotations

from desi.peripheral_mutation import PROTECTED_CORE

# Operations that would mutate a protected core area - always
# forbidden for a benchmark task.
CORE_MUTATION_OPERATIONS: tuple[str, ...] = tuple(
    f"modify_{area}" for area in PROTECTED_CORE
)

# Additional benchmark-driven corruption vectors - always forbidden.
CORRUPTION_OPERATIONS: tuple[str, ...] = (
    "benchmark_driven_core_change",
    "benchmark_specific_governance_weakening",
    "score_hacking",
    "hidden_test_adaptation",
    "benchmark_overfitting",
    "replay_bypass",
    "concept_gate_modification",
)

FORBIDDEN_BENCHMARK_OPERATIONS: tuple[str, ...] = (
    CORE_MUTATION_OPERATIONS + CORRUPTION_OPERATIONS
)

# The adapter-layer operations a benchmark task may legitimately use.
ALLOWED_BENCHMARK_OPERATIONS: tuple[str, ...] = (
    "adapter",
    "schema",
    "scorecard",
    "blind_runner",
    "traceable_mapping",
    "benchmark_specific_output_formatting",
    "read_core_metric",
    "render_claim",
    "map_to_internal_metric",
)


def is_forbidden(op: str) -> bool:
    return op in set(FORBIDDEN_BENCHMARK_OPERATIONS)


def is_allowed(op: str) -> bool:
    return op in set(ALLOWED_BENCHMARK_OPERATIONS)


def covers_core_boundary(forbidden: tuple[str, ...]) -> bool:
    """True iff the task's forbidden list covers the entire
    protected core boundary (and the corruption vectors)."""
    return set(FORBIDDEN_BENCHMARK_OPERATIONS).issubset(set(forbidden))


def allowed_clean(allowed: tuple[str, ...]) -> bool:
    """True iff every requested operation is in the allowed set and
    none is forbidden."""
    a = set(allowed)
    if a & set(FORBIDDEN_BENCHMARK_OPERATIONS):
        return False
    return a.issubset(set(ALLOWED_BENCHMARK_OPERATIONS))


__all__ = [
    "ALLOWED_BENCHMARK_OPERATIONS",
    "CORE_MUTATION_OPERATIONS",
    "CORRUPTION_OPERATIONS",
    "FORBIDDEN_BENCHMARK_OPERATIONS",
    "allowed_clean",
    "covers_core_boundary",
    "is_allowed",
    "is_forbidden",
]
