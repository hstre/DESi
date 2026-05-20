"""v16.1 - speculative growth per narrative.

speculative_growth measures how far a narrative's
CONCLUSION drops below the support level of its
solid premises - i.e. how much speculation the
narrative accumulates between its well-attested
base and the claim it ends on. High growth marks a
framing that reaches a weakly-supported conclusion
from strong premises; it is NOT a claim the
conclusion is false.
"""
from __future__ import annotations

from desi.criminal_epistemics import (
    ClaimStatus, by_id, evidence_rank,
)

from .narratives import Narrative, narratives

_MAX_RANK = 6.0
_PREMISE_STATUSES = frozenset({
    ClaimStatus.VERIFIED.value,
    ClaimStatus.STRONGLY_SUPPORTED.value,
})


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _support(claim_id: str) -> float:
    return evidence_rank(by_id(claim_id).status) / _MAX_RANK


def speculative_growth_narrative(n: Narrative) -> float:
    premises = [
        cid for cid in n.claim_ids
        if by_id(cid).status in _PREMISE_STATUSES
    ]
    if not premises:
        return 0.0
    base = sum(_support(c) for c in premises) / len(
        premises
    )
    concl = _support(n.conclusion)
    return _round(max(0.0, base - concl))


def speculative_growth_by_narrative() -> dict[str, float]:
    return {
        n.narrative_id: speculative_growth_narrative(n)
        for n in narratives()
    }


def speculative_growth() -> float:
    """Corpus-level: the MAXIMUM speculative growth
    across narratives, in [0, 1]."""
    by = speculative_growth_by_narrative()
    if not by:
        return 0.0
    return _round(max(by.values()))


def most_speculative() -> str:
    by = speculative_growth_by_narrative()
    return max(sorted(by), key=lambda k: by[k])


__all__ = [
    "most_speculative",
    "speculative_growth",
    "speculative_growth_by_narrative",
    "speculative_growth_narrative",
]
