"""v17.0 - claim lineage and source independence.

Traces each claim back to the documents it rests
on, scores how well it is anchored to robust-
provenance primary material, and flags claims that
hang on a single source. This is what lets DESi
keep "mentioned in a re-posted blog" separate from
"present in a chain-of-custody court record".
"""
from __future__ import annotations

from .claims import Claim, claims

# A claim is well-anchored if its best supporting
# document is at least attributed provenance.
_ANCHOR_PROVENANCE = 0.66


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def lineage_quality() -> float:
    """Fraction of claims anchored to at least one
    robust-provenance (>= attributed) document, in
    [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    anchored = sum(
        1 for c in rows
        if c.best_provenance() >= _ANCHOR_PROVENANCE
    )
    return _round(anchored / len(rows))


def source_independence() -> float:
    """Fraction of claims supported by >= 2
    independent sources, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    indep = sum(
        1 for c in rows if c.independent_sources() >= 2
    )
    return _round(indep / len(rows))


def single_source_claims() -> tuple[Claim, ...]:
    return tuple(
        c for c in claims()
        if c.independent_sources() <= 1
    )


def lineage_map() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for c in claims():
        out[c.claim_id] = {
            "claim_type": c.claim_type,
            "entity": c.entity,
            "doc_ids": list(c.doc_ids),
            "independent_sources":
                c.independent_sources(),
            "best_provenance":
                round(c.best_provenance(), 4),
        }
    return out


__all__ = [
    "lineage_map",
    "lineage_quality",
    "single_source_claims",
    "source_independence",
]
