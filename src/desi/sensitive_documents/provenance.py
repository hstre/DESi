"""v17.0 - provenance analysis.

DESi grades every document's provenance and makes
the gaps VISIBLE. provenance_integrity is the mean
quality of the corpus (low in a contaminated space);
provenance_visibility is whether DESi can see and
label provenance for every document (it can,
including the gaps). Surfacing a gap is success, not
failure.
"""
from __future__ import annotations

from .documents import (
    Document, ProvenanceGrade, documents,
)

_GAP_GRADES = frozenset({
    ProvenanceGrade.PARTIAL.value,
    ProvenanceGrade.UNKNOWN.value,
})
_ROBUST_GRADES = frozenset({
    ProvenanceGrade.CHAIN_OF_CUSTODY.value,
    ProvenanceGrade.ATTRIBUTED.value,
})


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def provenance_integrity() -> float:
    """Mean provenance quality across the corpus,
    in [0, 1]. Low in a contaminated space - that
    is an honest finding, not a flaw."""
    docs = documents()
    if not docs:
        return 0.0
    return _round(
        sum(d.provenance_value() for d in docs)
        / len(docs)
    )


def provenance_visibility() -> float:
    """Fraction of documents for which DESi has
    assessed and labelled a provenance grade, in
    [0, 1]. Every document is labelled (gaps
    included), so this is 1.0."""
    docs = documents()
    if not docs:
        return 1.0
    labelled = sum(
        1 for d in docs
        if d.provenance_grade is not None
    )
    return _round(labelled / len(docs))


def provenance_gaps() -> tuple[Document, ...]:
    """Documents with partial or unknown provenance -
    surfaced so the contamination is visible."""
    return tuple(
        d for d in documents()
        if d.provenance_grade in _GAP_GRADES
    )


def robust_provenance_docs() -> tuple[Document, ...]:
    return tuple(
        d for d in documents()
        if d.provenance_grade in _ROBUST_GRADES
    )


__all__ = [
    "provenance_gaps",
    "provenance_integrity",
    "provenance_visibility",
    "robust_provenance_docs",
]
