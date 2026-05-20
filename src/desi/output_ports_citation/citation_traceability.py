"""v25.2 - citation traceability and alignment.

Each citation edge must trace to a known external claim on one
end and a registered reference on the other; each claim must be
correctly aligned to its references; and every reference must be
used. This is what makes a citation an epistemic edge.
"""
from __future__ import annotations

from desi.output_ports_arxiv import external_claims

from .citations import (
    cited_keys, citation_edges, claim_ids, edges_for_claim,
)
from .phantom_detection import (
    is_phantom_ref, wrong_reference_assignment,
)
from .references import registered_keys


def citation_traceability() -> float:
    """Fraction of citation edges that resolve to both a known
    claim and a registered reference, in [0, 1]."""
    edges = citation_edges()
    if not edges:
        return 0.0
    claims = claim_ids()
    traced = sum(
        1 for e in edges
        if e.claim_id in claims and not is_phantom_ref(e.ref_key)
    )
    return round(traced / len(edges), 6)


def claim_reference_alignment() -> float:
    """Fraction of external claims correctly aligned: at least
    one reference, all registered, none misassigned, in
    [0, 1]."""
    claims = external_claims()
    if not claims:
        return 0.0
    misassigned = {a for a, _ in wrong_reference_assignment()}
    aligned = 0
    for c in claims:
        ok = (
            bool(edges_for_claim(c.claim_id))
            and all(
                not is_phantom_ref(k) for k in c.reference_keys
            )
            and c.claim_id not in misassigned
        )
        if ok:
            aligned += 1
    return round(aligned / len(claims), 6)


def reference_usage_integrity() -> float:
    """Fraction of registered references that are used by at
    least one citation edge, in [0, 1]."""
    keys = registered_keys()
    if not keys:
        return 0.0
    used = cited_keys()
    return round(len(keys & used) / len(keys), 6)


__all__ = [
    "citation_traceability",
    "claim_reference_alignment",
    "reference_usage_integrity",
]
