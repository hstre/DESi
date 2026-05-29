"""Projection-derived epistemic governance flags for SPL-core.

These are *mark-only* flags attached to a `CanonicalClaimCandidate` based on its
admissibility / emission outcome. They never change a claim's content or state;
they record *why* the projection layer treated a claim the way it did, so the
claim graph and governance can quarantine or down-weight without silently
dropping anything.

    projection_invalid       — the gate did not admit the candidate at all
                               (E0 / structural / empty_content / hallucinated_relation,
                               or a flag-model rejection).
    projection_high_entropy  — inadmissible specifically via E3 (h_norm ≥ τ₃):
                               the relational distribution was too flat.
    projection_uncertain     — admitted but not a clean singular emission: E2
                               (moderate entropy), or a flag-model "ambiguous"
                               rejection.
"""
from __future__ import annotations

from typing import Any

PROJECTION_INVALID = "projection_invalid"
PROJECTION_HIGH_ENTROPY = "projection_high_entropy"
PROJECTION_UNCERTAIN = "projection_uncertain"


def projection_flags(cand: Any) -> list[str]:
    """Return the projection governance flags for a CanonicalClaimCandidate."""
    flags: list[str] = []
    reason = cand.admission_reason or ""
    if not cand.admissible:
        flags.append(PROJECTION_INVALID)
        if cand.emission_rule == "E3":
            flags.append(PROJECTION_HIGH_ENTROPY)
        if "ambiguous" in reason:
            flags.append(PROJECTION_UNCERTAIN)
    elif cand.emission_rule == "E2":
        flags.append(PROJECTION_UNCERTAIN)
    return flags


__all__ = [
    "PROJECTION_HIGH_ENTROPY",
    "PROJECTION_INVALID",
    "PROJECTION_UNCERTAIN",
    "projection_flags",
]
