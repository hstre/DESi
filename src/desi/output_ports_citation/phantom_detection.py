"""v25.2 - phantom and misalignment detection.

Detects the failure modes of literature-as-decoration: phantom
citations (a citation to no registered reference), missing
citations (an external claim with no reference), unsupported
related-work claims, wrong reference assignment, and orphan
references.
"""
from __future__ import annotations

from desi.output_ports_arxiv import external_claims

from .citations import (
    CitationEdge, cited_keys, citation_edges, edges_for_claim,
)
from .references import is_registered, registered_keys


def is_phantom_ref(ref_key: str) -> bool:
    return not is_registered(ref_key)


def phantom_citations() -> tuple[str, ...]:
    """Citation edges pointing at an unregistered reference -
    must be empty."""
    return tuple(sorted(
        e.ref_key for e in citation_edges()
        if is_phantom_ref(e.ref_key)
    ))


def missing_citations() -> tuple[str, ...]:
    """External claims with no citation edge - must be empty."""
    return tuple(
        c.claim_id for c in external_claims()
        if not edges_for_claim(c.claim_id)
    )


def unsupported_related_work_claims() -> tuple[str, ...]:
    """External claims (related-work statements) whose declared
    references are not all registered - must be empty."""
    bad: list[str] = []
    for c in external_claims():
        if any(is_phantom_ref(k) for k in c.reference_keys):
            bad.append(c.claim_id)
    return tuple(sorted(bad))


def wrong_reference_assignment() -> tuple[tuple[str, str], ...]:
    """Citation edges whose ref is not among the claim's own
    declared references - must be empty."""
    declared = {
        c.claim_id: set(c.reference_keys)
        for c in external_claims()
    }
    bad: list[tuple[str, str]] = []
    for e in citation_edges():
        if e.ref_key not in declared.get(e.claim_id, set()):
            bad.append((e.claim_id, e.ref_key))
    return tuple(sorted(bad))


def orphan_references() -> tuple[str, ...]:
    """Registered references used by no citation edge - must be
    empty."""
    used = cited_keys()
    return tuple(sorted(registered_keys() - used))


def detects_synthetic_phantom() -> bool:
    """The detector must flag a deliberately unregistered key."""
    synthetic = CitationEdge("EC_synthetic", "___unregistered___")
    return is_phantom_ref(synthetic.ref_key)


def phantom_citation_detection() -> float:
    """1.0 iff there are no real phantom citations and the
    detector correctly flags a synthetic phantom."""
    checks = [
        not phantom_citations(),
        detects_synthetic_phantom(),
    ]
    return round(sum(1 for c in checks if c) / len(checks), 6)


__all__ = [
    "detects_synthetic_phantom",
    "is_phantom_ref",
    "missing_citations",
    "orphan_references",
    "phantom_citation_detection",
    "phantom_citations",
    "unsupported_related_work_claims",
    "wrong_reference_assignment",
]
