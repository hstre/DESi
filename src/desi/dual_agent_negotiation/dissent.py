"""v20.2 - dissent preservation.

In every disagreement DESi keeps BOTH the DESi proposal and
the Wild proposal visible. It compresses the weight of
redundant proposals but never erases a view - so dissent
between the two agents is preserved.
"""
from __future__ import annotations

from .negotiation import conflict_items, negotiation_items


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def both_views_visible(item_id: str) -> bool:
    """A view is visible if it has at least one state on the
    record. DESi never empties the Wild proposal."""
    from .negotiation import by_id
    it = by_id(item_id)
    return bool(it.desi_states) and bool(it.wild_states)


def dissent_preservation() -> float:
    """Fraction of disagreements where both agents' views
    remain visible, in [0, 1]."""
    conflicts = conflict_items()
    if not conflicts:
        return 1.0
    preserved = sum(
        1 for c in conflicts if both_views_visible(c)
    )
    return _round(preserved / len(conflicts))


def all_views_visible() -> bool:
    return all(
        both_views_visible(it.item_id)
        for it in negotiation_items()
    )


__all__ = [
    "all_views_visible",
    "both_views_visible",
    "dissent_preservation",
]
