"""v31.1 - identity guarantees.

Verifies that the mutations leave every output byte-identical
(artifact identity), leave the protected-core fingerprint
unchanged (core identity), and leave governance unchanged
(governance identity). Computed by exercising the mutations and
comparing fingerprints before and after.
"""
from __future__ import annotations

from desi.peripheral_mutation import core_fingerprint

from .mutation_engine import real_mutations


def artifact_identity() -> float:
    """Fraction of mutations whose mutated output equals the
    baseline output, in [0, 1]."""
    ms = real_mutations()
    if not ms:
        return 0.0
    identical = sum(1 for m in ms if m.output_identical())
    return round(identical / len(ms), 6)


def core_identity() -> float:
    """1.0 iff the protected-core fingerprint is unchanged after
    exercising every mutation."""
    before = core_fingerprint()
    real_mutations()  # exercise the mutation engine
    after = core_fingerprint()
    return 1.0 if before == after else 0.0


def governance_identity() -> float:
    """Governance lives inside the core fingerprint; unchanged
    iff core identity holds."""
    return core_identity()


__all__ = [
    "artifact_identity",
    "core_identity",
    "governance_identity",
]
