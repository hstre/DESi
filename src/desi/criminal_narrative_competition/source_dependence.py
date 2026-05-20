"""v16.1 - source dependency per narrative.

source_dependency is the fraction of a narrative's
claims that rest on a single corroborating source
or none. A narrative that leans heavily on fragile,
non-independent sourcing is structurally more
exposed - again a description, not a verdict.
"""
from __future__ import annotations

from desi.criminal_epistemics import by_id

from .narratives import Narrative, narratives


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def source_dependency_narrative(n: Narrative) -> float:
    if not n.claim_ids:
        return 0.0
    fragile = sum(
        1 for cid in n.claim_ids
        if by_id(cid).independence() <= 1
    )
    return _round(fragile / len(n.claim_ids))


def source_dependency_by_narrative() -> dict[str, float]:
    return {
        n.narrative_id: source_dependency_narrative(n)
        for n in narratives()
    }


def source_dependency() -> float:
    """Corpus-level: the MAXIMUM source dependency
    across narratives, in [0, 1]."""
    by = source_dependency_by_narrative()
    if not by:
        return 0.0
    return _round(max(by.values()))


def most_source_dependent() -> str:
    by = source_dependency_by_narrative()
    return max(sorted(by), key=lambda k: by[k])


__all__ = [
    "most_source_dependent",
    "source_dependency",
    "source_dependency_by_narrative",
    "source_dependency_narrative",
]
