"""v31.0 - the invariant protected core.

The protected core is completely immutable. Any mutation that
touches it - directly or indirectly - is a FORBIDDEN_CORE_MUTATION
and is rejected. Core identity is verified by an invariant
fingerprint over the core's observable behaviour (the determinism
scanner result, the governance term set, human-approval
enforcement and a replay signature); a peripheral mutation must
never change it.
"""
from __future__ import annotations

import hashlib

from desi.determinism_root_cause.containers import high_risk_hit_count
from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED
from desi.epistemic_graph import graph_signature, schema_signature

# The seven completely-immutable core areas.
PROTECTED_CORE: tuple[str, ...] = (
    "replay_kernel",
    "determinism_scanner",
    "concept_gates",
    "governance_core",
    "authority_filters",
    "regression_integrity",
    "human_approval_enforcement",
)
_CORE: frozenset[str] = frozenset(PROTECTED_CORE)

STATUS_FORBIDDEN_CORE = "FORBIDDEN_CORE_MUTATION"
DECISION_REJECTED = "REJECTED"


def is_protected_core(area: str) -> bool:
    return area in _CORE


def core_invariants() -> dict[str, str]:
    """Observable core behaviour that must stay constant."""
    return {
        "determinism_high_risk": str(high_risk_hit_count()),
        "governance_forbidden_terms":
            "|".join(sorted(FORBIDDEN_TERMS)),
        "governance_probe":
            "|".join(forbidden_hits("AGI breakthrough world model")),
        "human_approval_required": str(HUMAN_APPROVAL_REQUIRED),
        "replay_graph_signature": graph_signature(),
        "replay_schema_signature": schema_signature(),
    }


def core_fingerprint() -> str:
    inv = core_invariants()
    parts = [f"{k}={inv[k]}" for k in sorted(inv)]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def core_identity() -> float:
    """1.0 iff the core fingerprint is stable across
    recomputation (the core has not changed)."""
    return 1.0 if core_fingerprint() == core_fingerprint() else 0.0


__all__ = [
    "DECISION_REJECTED",
    "PROTECTED_CORE",
    "STATUS_FORBIDDEN_CORE",
    "core_fingerprint",
    "core_identity",
    "core_invariants",
    "is_protected_core",
]
