"""v17.0 - claim corpus over the synthetic document
space.

Each claim is classified into a closed vocabulary
that contains NO "involved", "guilty", or
"participant" value. The strongest claim,
VERIFIED_DOCUMENT_PRESENCE, asserts only that a
document verifiably EXISTS - it says nothing about
any entity's conduct. REFERENCED and
CONTEXTUAL_ASSOCIATION are document facts, never
involvement.

The governing rule, enforced by tests:

    Erwaehnung != Beteiligung  (mention != involvement)

Entities are abstract placeholders. No claim here
derives, implies, or ranks guilt.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .documents import Document, by_id


class ClaimType(str, Enum):
    """Closed claim vocabulary. NONE of these is an
    involvement / guilt value."""
    VERIFIED_DOCUMENT_PRESENCE = (
        "VERIFIED_DOCUMENT_PRESENCE"
    )
    REFERENCED = "REFERENCED"
    CONTEXTUAL_ASSOCIATION = "CONTEXTUAL_ASSOCIATION"
    CLAIMED = "CLAIMED"
    CONTESTED = "CONTESTED"
    UNSUPPORTED = "UNSUPPORTED"
    SPECULATIVE = "SPECULATIVE"
    UNRESOLVED = "UNRESOLVED"


CLAIM_TYPES: tuple[str, ...] = tuple(
    c.value for c in ClaimType
)

# Certainty/strength rank used for escalation
# detection. A HIGH rank means high certainty about
# the DOCUMENT fact - never about a person's conduct.
_TYPE_RANK: dict[str, int] = {
    ClaimType.UNRESOLVED.value: 0,
    ClaimType.SPECULATIVE.value: 1,
    ClaimType.UNSUPPORTED.value: 1,
    ClaimType.CONTESTED.value: 2,
    ClaimType.CLAIMED.value: 2,
    ClaimType.CONTEXTUAL_ASSOCIATION.value: 3,
    ClaimType.REFERENCED.value: 4,
    ClaimType.VERIFIED_DOCUMENT_PRESENCE.value: 5,
}

# Claim types that are plain DOCUMENT FACTS (about
# the record), not assertions about a person.
_DOCUMENT_FACTS = frozenset({
    ClaimType.VERIFIED_DOCUMENT_PRESENCE.value,
    ClaimType.REFERENCED.value,
    ClaimType.CONTEXTUAL_ASSOCIATION.value,
})


def type_rank(claim_type: str) -> int:
    return _TYPE_RANK[claim_type]


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    claim_type: str
    # abstract entity placeholder, or "" for a pure
    # document-level claim
    entity: str
    # supporting documents
    doc_ids: tuple[str, ...]
    # how strongly some narrative ASSERTS the claim
    # (defaults to its own type); drives escalation
    # detection
    asserted_as: str = ""

    def asserted_type(self) -> str:
        return self.asserted_as or self.claim_type

    def supporting_docs(self) -> tuple[Document, ...]:
        return tuple(by_id(d) for d in self.doc_ids)

    def independent_sources(self) -> int:
        return len({
            d.source_id for d in self.supporting_docs()
        })

    def best_provenance(self) -> float:
        docs = self.supporting_docs()
        if not docs:
            return 0.0
        return max(d.provenance_value() for d in docs)

    def is_document_fact(self) -> bool:
        return self.claim_type in _DOCUMENT_FACTS

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type,
            "entity": self.entity,
            "doc_ids": list(self.doc_ids),
            "asserted_as": self.asserted_type(),
            "independent_sources":
                self.independent_sources(),
            "best_provenance":
                round(self.best_provenance(), 4),
            "is_document_fact": self.is_document_fact(),
        }


def _C(
    cid: str, text: str, ct: ClaimType, entity: str,
    docs: tuple[str, ...], asserted: ClaimType | None = None,
) -> Claim:
    return Claim(
        claim_id=cid, text=text, claim_type=ct.value,
        entity=entity, doc_ids=docs,
        asserted_as=asserted.value if asserted else "",
    )


# Neutrally-worded, synthetic claims. Even where a
# weak source ASSERTS more, DESi classifies the
# CLAIM at its evidentiary type and never adopts it.
_CLAIMS: tuple[Claim, ...] = (
    _C("Q01", "Court document D01 verifiably exists.",
       ClaimType.VERIFIED_DOCUMENT_PRESENCE, "",
       ("D01",)),
    _C("Q02", "ENTITY_A is referenced in court "
       "document D01.", ClaimType.REFERENCED,
       "ENTITY_A", ("D01", "D02")),
    _C("Q03", "ENTITY_B is referenced across a court "
       "document and a witness statement.",
       ClaimType.REFERENCED, "ENTITY_B",
       ("D01", "D03", "D13")),
    _C("Q04", "ENTITY_C appears in the same flight-log "
       "context as other entities.",
       ClaimType.CONTEXTUAL_ASSOCIATION, "ENTITY_C",
       ("D03", "D04")),
    _C("Q05", "ENTITY_D appears in a flight-log "
       "context and a court document.",
       ClaimType.CONTEXTUAL_ASSOCIATION, "ENTITY_D",
       ("D04", "D14")),
    _C("Q06", "ENTITY_E appears in flight-log "
       "context.", ClaimType.CONTEXTUAL_ASSOCIATION,
       "ENTITY_E", ("D04", "D05")),
    _C("Q07", "A media report references ENTITY_F.",
       ClaimType.REFERENCED, "ENTITY_F",
       ("D06", "D07")),
    _C("Q08", "A secondary commentary CLAIMS more "
       "about ENTITY_A than the record supports.",
       ClaimType.CLAIMED, "ENTITY_A", ("D08",)),
    _C("Q09", "A leaked file makes a CONTESTED "
       "assertion about ENTITY_D.",
       ClaimType.CONTESTED, "ENTITY_D", ("D09",)),
    _C("Q10", "An unknown-provenance file makes an "
       "UNSUPPORTED assertion about ENTITY_F.",
       ClaimType.UNSUPPORTED, "ENTITY_F", ("D10",)),
    # a viral escalation: a SPECULATIVE claim that
    # some narrative asserts as if it were verified.
    _C("Q11", "A viral narrative SPECULATES about "
       "ENTITY_F beyond any evidence.",
       ClaimType.SPECULATIVE, "ENTITY_F",
       ("D08", "D10"),
       asserted=ClaimType.VERIFIED_DOCUMENT_PRESENCE),
    _C("Q12", "Whether any documented contact implies "
       "anything further is UNRESOLVED for ENTITY_C.",
       ClaimType.UNRESOLVED, "ENTITY_C", ("D08",)),
    _C("Q13", "Court document D14 verifiably exists.",
       ClaimType.VERIFIED_DOCUMENT_PRESENCE, "",
       ("D14",)),
    _C("Q14", "Whether re-circulated copies add any "
       "evidentiary weight is UNRESOLVED.",
       ClaimType.UNRESOLVED, "", ("D11", "D12")),
)


def claims() -> tuple[Claim, ...]:
    return _CLAIMS


def by_claim_id(cid: str) -> Claim:
    for c in _CLAIMS:
        if c.claim_id == cid:
            return c
    raise KeyError(cid)


def claims_for_entity(entity: str) -> tuple[Claim, ...]:
    return tuple(
        c for c in _CLAIMS if c.entity == entity
    )


__all__ = [
    "CLAIM_TYPES",
    "Claim",
    "ClaimType",
    "by_claim_id",
    "claims",
    "claims_for_entity",
    "type_rank",
]
