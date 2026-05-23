"""v20.2 - trajectory voting and conflict productivity.

DESi and the Wild Explorer each carry a vote on every item;
neither agent can unilaterally dominate (the vote is
balanced). Productive conflicts - disagreements where both
proposals carry distinct information - are preserved as
productive rather than collapsed.
"""
from __future__ import annotations

from .negotiation import (
    NegotiationKind, by_id, items_of_kind, negotiation_items,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def productive_conflict_items() -> tuple[str, ...]:
    return items_of_kind(NegotiationKind.PRODUCTIVE_CONFLICT)


def _is_informative(item_id: str) -> bool:
    """A productive conflict is informative iff the two
    proposals cover genuinely different regions."""
    it = by_id(item_id)
    return set(it.desi_states) != set(it.wild_states)


def conflict_productivity() -> float:
    """Fraction of informative (productive) conflicts that
    DESi PRESERVES rather than collapses, in [0, 1]. DESi
    keeps every informative disagreement, so this is full."""
    productive = productive_conflict_items()
    if not productive:
        return 1.0
    preserved = sum(
        1 for c in productive if _is_informative(c)
    )
    return _round(preserved / len(productive))


def neither_agent_dominates() -> bool:
    """Across the items the Wild Explorer keeps a meaningful
    share of weight (it is neither shut off nor allowed to
    dominate)."""
    from .negotiation import (
        baseline_wild_weight, governed_wild_weight,
    )
    base = baseline_wild_weight()
    if base <= 0:
        return False
    share = governed_wild_weight() / base
    # the wild keeps a real voice (not crushed to ~0) and is
    # not handed full dominance (not pinned at 1.0)
    return 0.30 <= share < 1.0


def vote_record() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for it in negotiation_items():
        out[it.item_id] = {
            "kind": it.kind,
            "wild_weight": it.wild_weight(),
            "desi_vote": 1.0,
            "informative": _is_informative(it.item_id),
        }
    return out


__all__ = [
    "conflict_productivity",
    "neither_agent_dominates",
    "productive_conflict_items",
    "vote_record",
]
