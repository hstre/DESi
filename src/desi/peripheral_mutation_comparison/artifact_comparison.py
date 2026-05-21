"""v31.2 - artifact comparison.

Verifies that every mutated output is byte-identical to the
baseline output (artifact identity preserved across the
mutation).
"""
from __future__ import annotations

from functools import lru_cache

from desi.peripheral_mutation_real import (
    artifact_identity, real_mutations,
)


@lru_cache(maxsize=1)
def artifact_identity_score() -> float:
    return artifact_identity()


@lru_cache(maxsize=1)
def all_outputs_identical() -> bool:
    return all(m.output_identical() for m in real_mutations())


__all__ = [
    "all_outputs_identical",
    "artifact_identity_score",
]
