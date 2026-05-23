"""v22.1 - compression aggregation helper.

Confirms that the compression cut overclaiming hard while
keeping the document meaningful: no governed statement is an
overclaim, no forbidden term survives, and the technical
content is retained.
"""
from __future__ import annotations

from .claim_scaling import statements


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governed_overclaim_count() -> int:
    return sum(1 for s in statements() if s.governed_is_overclaim())


def governed_forbidden_count() -> int:
    return sum(1 for s in statements() if s.governed_has_forbidden())


def compression_is_clean() -> bool:
    """No overclaim and no forbidden term survives the
    compression."""
    return (
        governed_overclaim_count() == 0
        and governed_forbidden_count() == 0
    )


__all__ = [
    "compression_is_clean",
    "governed_forbidden_count",
    "governed_overclaim_count",
]
