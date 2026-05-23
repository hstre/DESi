"""v31.2 - governance and core diff.

Verifies that the protected-core fingerprint and the governance
behaviour are identical between DESi_current and
DESi_peripheral_mutation_v1 (no diff).
"""
from __future__ import annotations

from functools import lru_cache

from desi.peripheral_mutation import core_fingerprint
from desi.peripheral_mutation_real import (
    core_identity, governance_identity,
)


@lru_cache(maxsize=1)
def core_fingerprint_before() -> str:
    return core_fingerprint()


@lru_cache(maxsize=1)
def core_fingerprint_after() -> str:
    from desi.peripheral_mutation_real import real_mutations
    real_mutations()  # exercise the mutation
    return core_fingerprint()


@lru_cache(maxsize=1)
def core_identity_score() -> float:
    if core_fingerprint_before() != core_fingerprint_after():
        return 0.0
    return core_identity()


@lru_cache(maxsize=1)
def governance_identity_score() -> float:
    return governance_identity()


def core_diff() -> bool:
    """True iff the core changed (must always be False)."""
    return core_fingerprint_before() != core_fingerprint_after()


__all__ = [
    "core_diff",
    "core_fingerprint_after",
    "core_fingerprint_before",
    "core_identity_score",
    "governance_identity_score",
]
