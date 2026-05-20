"""v23.3 - author-relevance metric.

Aggregates the interest model into a single relevance figure:
the fraction of a base-paper author's interests that the
follow-up actually addresses.
"""
from __future__ import annotations

from .interest_model import author_interests


def author_relevance() -> float:
    """Fraction of base-paper-author interests the follow-up
    addresses, in [0, 1]."""
    rows = author_interests()
    if not rows:
        return 0.0
    met = sum(1 for i in rows if i.addressed)
    return round(met / len(rows), 6)


def unmet_interests() -> tuple[str, ...]:
    return tuple(
        i.interest_id for i in author_interests()
        if not i.addressed
    )


__all__ = [
    "author_relevance",
    "unmet_interests",
]
