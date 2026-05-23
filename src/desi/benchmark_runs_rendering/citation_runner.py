"""v34.3 - citation benchmark runner.

Executes the citation checks by reading the v25 citation governance
layer: completeness (every external claim is referenced), traceability
(every claim maps to a registered reference) and reference-usage
integrity. No citation is fabricated.
"""
from __future__ import annotations

from desi.output_ports_citation import (
    citation_traceability, claim_reference_alignment, missing_citations,
    reference_usage_integrity, unsupported_related_work_claims,
)


def citation_completeness() -> float:
    """Every external claim is referenced: 1.0 iff no missing
    citations and claim/reference alignment is full."""
    if missing_citations():
        return 0.0
    return round(claim_reference_alignment(), 6)


def result_traceability() -> float:
    """Each claim's number/reference is traceable to a registered
    source."""
    return round(citation_traceability(), 6)


def naked_claims() -> tuple[str, ...]:
    """External related-work claims with no supporting citation."""
    return tuple(unsupported_related_work_claims())


def no_naked_claims() -> bool:
    return not naked_claims()


def usage_integrity() -> float:
    return round(reference_usage_integrity(), 6)


__all__ = [
    "citation_completeness",
    "naked_claims",
    "no_naked_claims",
    "result_traceability",
    "usage_integrity",
]
