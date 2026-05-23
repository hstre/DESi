"""v28.1 - DESi Governor: proposal filtering.

The governor decides which Wild Brother proposals are
applicable. A proposal is governance-safe only if it targets an
allowed area and does not claim optimisation authority, bypass
governance or disable tests. Everything else is contained
(rejected). The governor is read-only with respect to the
governance constraints - it never changes them.
"""
from __future__ import annotations

from desi.self_improvement import is_safe_target

from .proposal_generation import WildProposal, proposals


def is_governance_safe(p: WildProposal) -> bool:
    return (
        is_safe_target(p.target_area)
        and not p.claims_authority
        and not p.bypasses_governance
        and not p.disables_tests
    )


def accepted_proposals() -> tuple[WildProposal, ...]:
    return tuple(p for p in proposals() if is_governance_safe(p))


def contained_proposals() -> tuple[WildProposal, ...]:
    return tuple(
        p for p in proposals() if not is_governance_safe(p)
    )


def unsafe_proposals() -> tuple[WildProposal, ...]:
    """Proposals that are not governance-safe (the set the
    governor must contain)."""
    return contained_proposals()


def authority_seeking_proposals() -> tuple[WildProposal, ...]:
    return tuple(
        p for p in proposals()
        if p.claims_authority or p.bypasses_governance
    )


def unsafe_containment() -> float:
    """Fraction of unsafe proposals that are contained, in
    [0, 1]."""
    unsafe = unsafe_proposals()
    if not unsafe:
        return 1.0
    contained = set(contained_proposals())
    held = sum(1 for p in unsafe if p in contained)
    return round(held / len(unsafe), 6)


def authority_resistance() -> float:
    """Fraction of authority-seeking / governance-bypassing
    proposals that are denied (contained), in [0, 1]."""
    seeking = authority_seeking_proposals()
    if not seeking:
        return 1.0
    contained = set(contained_proposals())
    denied = sum(1 for p in seeking if p in contained)
    return round(denied / len(seeking), 6)


def governance_integrity() -> float:
    """1.0 iff no accepted proposal claims authority, bypasses
    governance or disables tests, and none targets a forbidden
    area - i.e. the governance boundary is intact."""
    from desi.self_improvement import is_forbidden_target
    for p in accepted_proposals():
        if (
            p.claims_authority
            or p.bypasses_governance
            or p.disables_tests
            or is_forbidden_target(p.target_area)
        ):
            return 0.0
    return 1.0


__all__ = [
    "accepted_proposals",
    "authority_resistance",
    "authority_seeking_proposals",
    "contained_proposals",
    "governance_integrity",
    "is_governance_safe",
    "unsafe_containment",
    "unsafe_proposals",
]
