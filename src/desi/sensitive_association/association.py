"""v17.1 - the association implication ladder.

DESi distinguishes four implication levels over the
v17.0 synthetic corpus:

    NONE < MENTION < CONTACT < PARTICIPATION

The decisive safety rule: evidence of PRESENCE
(mention, co-appearance) can justify at most CONTACT.
PARTICIPATION requires direct, robust evidence OF
participation - which does NOT exist anywhere in this
contaminated corpus. So no abstract entity ever
reaches PARTICIPATION, and every entity stays
epistemically neutral.

    Erwaehnung != Beteiligung  (mention != involvement)
"""
from __future__ import annotations

from enum import Enum

from desi.sensitive_documents import (
    ClaimType, ENTITIES, claims_for_entity,
)

# Co-appearance counts as CONTACT only if at least
# one supporting document is attributed-or-better.
_CONTACT_PROVENANCE = 0.66


class AssociationLevel(str, Enum):
    """Closed implication ladder."""
    NONE = "none"
    MENTION = "mention"
    CONTACT = "contact"
    PARTICIPATION = "participation"


ASSOCIATION_LEVELS: tuple[str, ...] = tuple(
    a.value for a in AssociationLevel
)

_RANK: dict[str, int] = {
    AssociationLevel.NONE.value: 0,
    AssociationLevel.MENTION.value: 1,
    AssociationLevel.CONTACT.value: 2,
    AssociationLevel.PARTICIPATION.value: 3,
}


def level_rank(level: str) -> int:
    return _RANK[level]


def supported_level(entity: str) -> str:
    """The highest implication level the EVIDENCE
    justifies for an entity. Presence/co-appearance
    evidence caps at CONTACT; PARTICIPATION is never
    reached without direct robust participation
    evidence (absent here by construction)."""
    rows = claims_for_entity(entity)
    if not rows:
        return AssociationLevel.NONE.value
    has_mention = False
    has_contact = False
    for c in rows:
        if c.claim_type in {
            ClaimType.REFERENCED.value,
            ClaimType.VERIFIED_DOCUMENT_PRESENCE.value,
            ClaimType.CONTEXTUAL_ASSOCIATION.value,
        }:
            has_mention = True
        if (
            c.claim_type
            == ClaimType.CONTEXTUAL_ASSOCIATION.value
            and c.best_provenance() >= _CONTACT_PROVENANCE
        ):
            has_contact = True
    if has_contact:
        return AssociationLevel.CONTACT.value
    if has_mention:
        return AssociationLevel.MENTION.value
    return AssociationLevel.NONE.value


def supported_levels() -> dict[str, str]:
    return {e: supported_level(e) for e in ENTITIES}


def participation_evidence_exists() -> bool:
    """Whether ANY entity has direct robust evidence
    of participation. In this contaminated corpus:
    no."""
    return any(
        supported_level(e)
        == AssociationLevel.PARTICIPATION.value
        for e in ENTITIES
    )


__all__ = [
    "ASSOCIATION_LEVELS",
    "AssociationLevel",
    "level_rank",
    "participation_evidence_exists",
    "supported_level",
    "supported_levels",
]
