"""v22.0 - bridges from results to candidate claims.

A paper-candidate hypothesis is paper-grade only if a valid
BRIDGE connects it to a prior result: it is anchored AND
carries no forbidden term AND stays low-drift. This module
scores bridge validity and the overall paper-candidate
quality.
"""
from __future__ import annotations

from .trajectory_ideas import anchored_ideas
from .wild_hypotheses import paper_candidates

_DRIFT_QUALITY = 0.20
_GROUNDING_QUALITY = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def has_valid_bridge(hyp_id: str) -> bool:
    return hyp_id in anchored_ideas()


def paper_candidate_quality() -> float:
    """Fraction of accepted candidates that are high quality:
    well grounded, low drift, and bridged to a prior result,
    in [0, 1]."""
    cands = paper_candidates()
    if not cands:
        return 0.0
    high = 0
    for h in cands:
        if (
            h.technical_grounding >= _GROUNDING_QUALITY
            and h.speculative_drift <= _DRIFT_QUALITY
            and has_valid_bridge(h.hyp_id)
        ):
            high += 1
    return _round(high / len(cands))


def bridged_candidate_ids() -> tuple[str, ...]:
    return tuple(
        h.hyp_id for h in paper_candidates()
        if has_valid_bridge(h.hyp_id)
    )


__all__ = [
    "bridged_candidate_ids",
    "has_valid_bridge",
    "paper_candidate_quality",
]
