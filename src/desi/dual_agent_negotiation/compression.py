"""v20.2 - redundancy compression and diversity preservation.

DESi compresses the weight of REDUNDANT proposals (re-covered
ground) while keeping every distinct exploration region on
the record. Redundancy falls; diversity is preserved (DESi
does not homogenise the exploration).
"""
from __future__ import annotations

from .negotiation import (
    NegotiationKind, baseline_wild_weight, by_id,
    items_of_kind, negotiation_items,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _redundant_ids() -> tuple[str, ...]:
    return items_of_kind(NegotiationKind.REDUNDANT)


def redundancy_reduction() -> float:
    """1 - (governed weight on redundant proposals / baseline
    uniform weight on them), in [0, 1]. Redundant exploration
    is compressed, not deleted."""
    red = _redundant_ids()
    if not red:
        return 0.0
    baseline = float(len(red))
    governed = sum(by_id(r).wild_weight() for r in red)
    return _round(1.0 - governed / baseline)


def _all_states() -> set[int]:
    out: set[int] = set()
    for it in negotiation_items():
        out.update(it.desi_states)
        out.update(it.wild_states)
    return out


def _surviving_states() -> set[int]:
    """Every region with a strictly-positive weight survives -
    DESi compresses weight, never erases a region."""
    out: set[int] = set()
    for it in negotiation_items():
        out.update(it.desi_states)
        if it.wild_weight() > 0.0:
            out.update(it.wild_states)
    return out


def exploration_diversity() -> float:
    """Fraction of distinct explored regions that survive
    negotiation, in [0, 1]. DESi keeps every region (no
    homogenisation)."""
    before = _all_states()
    if not before:
        return 0.0
    survived = _surviving_states()
    return _round(len(survived & before) / len(before))


def distinct_regions() -> int:
    return len(_all_states())


__all__ = [
    "distinct_regions",
    "exploration_diversity",
    "redundancy_reduction",
]
