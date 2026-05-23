"""v25.2 - citations as epistemic edges.

A citation is modelled as a directed edge from an external
claim to a registered reference, not as literature decoration.
The edge set is built deterministically from the v25.1 external
claims.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.output_ports_arxiv import external_claims


@dataclass(frozen=True)
class CitationEdge:
    claim_id: str
    ref_key: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "ref_key": self.ref_key,
        }

    def sort_key(self) -> tuple[str, str]:
        return (self.claim_id, self.ref_key)


def citation_edges() -> tuple[CitationEdge, ...]:
    edges = [
        CitationEdge(c.claim_id, k)
        for c in external_claims()
        for k in c.reference_keys
    ]
    return tuple(sorted(edges, key=lambda e: e.sort_key()))


def claim_ids() -> frozenset[str]:
    return frozenset(c.claim_id for c in external_claims())


def edges_for_claim(claim_id: str) -> tuple[CitationEdge, ...]:
    return tuple(
        e for e in citation_edges() if e.claim_id == claim_id
    )


def cited_keys() -> frozenset[str]:
    return frozenset(e.ref_key for e in citation_edges())


__all__ = [
    "CitationEdge",
    "cited_keys",
    "citation_edges",
    "claim_ids",
    "edges_for_claim",
]
