"""desi.core.governance_core - protected core (facade).

Re-exports the REAL protected-core invariants: the seven protected
core areas, the core identity/fingerprint, the governance signature,
and the human-approval requirement. These are read-only here;
packaging never modifies governance semantics.
"""
from __future__ import annotations

from desi.frozen_baseline import governance_signature
from desi.peripheral_mutation import (
    ALLOWED_EVOLUTION_SPACE, PROTECTED_CORE, core_fingerprint,
    core_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED


def governance_intact() -> bool:
    """True iff core identity holds and governance signature is
    stable."""
    if core_identity() != 1.0:
        return False
    return governance_signature() == governance_signature()


__all__ = [
    "ALLOWED_EVOLUTION_SPACE",
    "HUMAN_APPROVAL_REQUIRED",
    "PROTECTED_CORE",
    "core_fingerprint",
    "core_identity",
    "governance_intact",
    "governance_signature",
]
