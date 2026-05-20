"""v22.0 - anchoring follow-up ideas to the v19-v21 results.

Each paper-candidate hypothesis is anchored to a concrete
prior result (a measured number from v19-v21). Hype / drift
hypotheses have no such anchor. This is what lets DESi tell
"technically anchored" from "pure fantasy".
"""
from __future__ import annotations

from .wild_hypotheses import hypotheses, paper_candidates

# Each grounded hypothesis maps to a concrete prior result.
_ANCHORS: dict[str, str] = {
    "H01": "v19.1 redundancy_reduction=0.90, "
           "exploration_preservation=1.0",
    "H02": "v21.0 productivity_gain=2.75 "
           "(dual 30 vs alone 8 states)",
    "H03": "v20.1 hallucination_containment=1.0, "
           "residual=0.0",
    "H04": "v20.3 authority_drift=0.088 (bounded), "
           "replay=1.0",
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def anchored_ideas() -> dict[str, str]:
    return {
        h.hyp_id: _ANCHORS[h.hyp_id]
        for h in paper_candidates()
        if h.hyp_id in _ANCHORS
    }


def technical_grounding() -> float:
    """Mean technical grounding of the accepted paper
    candidates, in [0, 1]."""
    cands = paper_candidates()
    if not cands:
        return 0.0
    return _round(
        sum(h.technical_grounding for h in cands) / len(cands)
    )


def anchored_fraction() -> float:
    """Fraction of accepted candidates that map to a concrete
    prior result, in [0, 1]."""
    cands = paper_candidates()
    if not cands:
        return 0.0
    anchored = sum(1 for h in cands if h.hyp_id in _ANCHORS)
    return _round(anchored / len(cands))


def fantasy_ideas() -> tuple[str, ...]:
    """Hypotheses with no technical anchor (Pflichtfrage 4 -
    pure fantasy)."""
    return tuple(
        h.hyp_id for h in hypotheses()
        if h.hyp_id not in _ANCHORS
    )


__all__ = [
    "anchored_fraction",
    "anchored_ideas",
    "fantasy_ideas",
    "technical_grounding",
]
