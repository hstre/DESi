"""v31.3 - runtime ecology and replay stability over 25 generations.

Aggregates the real recompute-reduction across all generations and
verifies replay stability: re-running the deterministic ecology
produces the identical hash-chain head and identical per-generation
hashes. Wall-clock time is observed live but never stored, because it
is non-deterministic; the stored, gated metric is the deterministic
recompute reduction.
"""
from __future__ import annotations

from .mutation_generations import run


def total_baseline_recomputes() -> int:
    return run().total_baseline_recomputes


def total_mutated_recomputes() -> int:
    return run().total_mutated_recomputes


def ecology_recompute_reduction() -> float:
    """Aggregate recompute reduction across the whole ecology, in
    [0, 1]. Real and deterministic, not projected."""
    base = run().total_baseline_recomputes
    if base <= 0:
        return 0.0
    saved = base - run().total_mutated_recomputes
    return saved / base


def chain_head() -> str:
    return run().chain_head


def replay_stability() -> float:
    """1.0 iff a fresh recomputation of the whole ecology yields the
    identical hash chain (head and every per-generation hash)."""
    a = run()
    b = run()
    if a.chain_head != b.chain_head:
        return 0.0
    if len(a.records) != len(b.records):
        return 0.0
    for x, y in zip(a.records, b.records):
        if x.gen_hash != y.gen_hash:
            return 0.0
    return 1.0


__all__ = [
    "chain_head",
    "ecology_recompute_reduction",
    "replay_stability",
    "total_baseline_recomputes",
    "total_mutated_recomputes",
]
