"""v25.1 - citation rules for the arXiv port.

Every external claim (a statement about prior work) must point
at a registered reference; every registered reference must be
used by an external claim. This treats citations as epistemic
edges, not literature decoration, and makes phantom citations
and unreferenced related-work claims detectable.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.output_ports import BASE_PAPER_REF

from .reference_manager import is_registered, reference_keys


@dataclass(frozen=True)
class ExternalClaim:
    claim_id: str
    text: str
    reference_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "reference_keys": list(self.reference_keys),
        }


_EXTERNAL_CLAIMS: tuple[ExternalClaim, ...] = (
    ExternalClaim(
        "EC1",
        "The base paper studies in-context reinforcement "
        "learning for variable action spaces and skill "
        "stitching.",
        (BASE_PAPER_REF,)),
    ExternalClaim(
        "EC2",
        "The base paper notes, in its Section 4.6 limitations, "
        "open exploration problems: exploration collapse, "
        "sparse-reward failure and repetitive trajectories.",
        (BASE_PAPER_REF,)),
    ExternalClaim(
        "EC3",
        "We position this work as a complementary follow-up to "
        "the base paper's open exploration question.",
        (BASE_PAPER_REF,)),
)


def external_claims() -> tuple[ExternalClaim, ...]:
    return _EXTERNAL_CLAIMS


def cited_reference_keys() -> frozenset[str]:
    keys: set[str] = set()
    for c in _EXTERNAL_CLAIMS:
        keys.update(c.reference_keys)
    return frozenset(keys)


def phantom_citations() -> tuple[str, ...]:
    """Citation keys used by a claim that resolve to no
    registered reference - must be empty."""
    bad: set[str] = set()
    for c in _EXTERNAL_CLAIMS:
        for k in c.reference_keys:
            if not is_registered(k):
                bad.add(k)
    return tuple(sorted(bad))


def unreferenced_external_claims() -> tuple[str, ...]:
    """External claims that carry no reference - must be
    empty."""
    return tuple(
        c.claim_id for c in _EXTERNAL_CLAIMS
        if not c.reference_keys
    )


def unused_references() -> tuple[str, ...]:
    """Registered references never used by a claim - must be
    empty (references are edges, not decoration)."""
    cited = cited_reference_keys()
    return tuple(sorted(reference_keys() - cited))


def base_paper_cited() -> bool:
    return BASE_PAPER_REF in cited_reference_keys()


def citation_completeness() -> float:
    """1.0 iff the base paper is cited, there are no phantom
    citations, every external claim is referenced and every
    reference is used."""
    checks = [
        base_paper_cited(),
        not phantom_citations(),
        not unreferenced_external_claims(),
        not unused_references(),
    ]
    return round(sum(1 for c in checks if c) / len(checks), 6)


__all__ = [
    "ExternalClaim",
    "base_paper_cited",
    "cited_reference_keys",
    "citation_completeness",
    "external_claims",
    "phantom_citations",
    "unreferenced_external_claims",
    "unused_references",
]
