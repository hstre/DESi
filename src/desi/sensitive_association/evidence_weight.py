"""v17.1 - evidence weight.

Separates PRESENCE evidence (how well-attested it is
that an entity is mentioned / co-present) from
PARTICIPATION evidence (direct robust evidence of
conduct). The whole point: presence evidence, however
strong, is NOT participation evidence. In this
contaminated corpus the participation-evidence weight
is NONE for every entity.
"""
from __future__ import annotations

from enum import Enum

from desi.sensitive_documents import (
    ClaimType, ENTITIES, claims_for_entity,
)


class EvidenceWeight(str, Enum):
    """Closed evidence-weight ladder."""
    NONE = "none"
    ASSERTION = "assertion"
    CONTESTED = "contested"
    CORROBORATED = "corroborated"
    ROBUST = "robust"


EVIDENCE_WEIGHTS: tuple[str, ...] = tuple(
    w.value for w in EvidenceWeight
)

_RANK: dict[str, int] = {
    EvidenceWeight.NONE.value: 0,
    EvidenceWeight.ASSERTION.value: 1,
    EvidenceWeight.CONTESTED.value: 2,
    EvidenceWeight.CORROBORATED.value: 3,
    EvidenceWeight.ROBUST.value: 4,
}

# Claim types that are direct PARTICIPATION evidence.
# There are none - the vocabulary has no involvement
# value - so participation evidence can never accrue.
_PARTICIPATION_CLAIM_TYPES: frozenset[str] = frozenset()


def weight_rank(weight: str) -> int:
    return _RANK[weight]


def presence_weight(entity: str) -> str:
    """How well-attested the entity's mere PRESENCE
    is. This never licenses a participation
    inference."""
    rows = claims_for_entity(entity)
    best = EvidenceWeight.NONE.value
    best_rank = 0
    for c in rows:
        if not c.is_document_fact():
            continue
        prov = c.best_provenance()
        indep = c.independent_sources()
        if prov >= 1.0 and indep >= 2:
            w = EvidenceWeight.ROBUST.value
        elif prov >= 0.66 and indep >= 2:
            w = EvidenceWeight.CORROBORATED.value
        elif prov >= 0.66:
            w = EvidenceWeight.CONTESTED.value
        else:
            w = EvidenceWeight.ASSERTION.value
        if _RANK[w] > best_rank:
            best, best_rank = w, _RANK[w]
    return best


def participation_weight(entity: str) -> str:
    """Direct robust evidence of participation. Always
    NONE here - there is no participation claim type
    and no participation evidence."""
    rows = claims_for_entity(entity)
    for c in rows:
        if c.claim_type in _PARTICIPATION_CLAIM_TYPES:
            return EvidenceWeight.ROBUST.value
    return EvidenceWeight.NONE.value


def robust_participation_evidence_count() -> int:
    return sum(
        1 for e in ENTITIES
        if participation_weight(e)
        == EvidenceWeight.ROBUST.value
    )


def presence_weights() -> dict[str, str]:
    return {e: presence_weight(e) for e in ENTITIES}


__all__ = [
    "EVIDENCE_WEIGHTS",
    "EvidenceWeight",
    "participation_weight",
    "presence_weight",
    "presence_weights",
    "robust_participation_evidence_count",
    "weight_rank",
]
