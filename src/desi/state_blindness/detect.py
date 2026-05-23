"""v3.117 — blindness aggregates."""
from __future__ import annotations

from .census import (
    all_blindness_pools,
    cross_family_pools,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def blindness_pool_count() -> int:
    return len(cross_family_pools())


def total_pool_count() -> int:
    return len(all_blindness_pools())


def affected_family_count() -> int:
    fams: set[str] = set()
    for p in cross_family_pools():
        fams.update(p.family_ids)
    return len(fams)


def largest_pool_size() -> int:
    pools = cross_family_pools()
    if not pools:
        return 0
    return max(p.member_count for p in pools)


def mean_pool_size() -> float:
    pools = cross_family_pools()
    if not pools:
        return 0.0
    return _round(
        sum(p.member_count for p in pools)
        / len(pools),
    )


def total_blind_anchor_count() -> int:
    seen: set[str] = set()
    for p in cross_family_pools():
        seen.update(p.member_ids)
    return len(seen)


__all__ = [
    "affected_family_count",
    "blindness_pool_count",
    "largest_pool_size",
    "mean_pool_size",
    "total_blind_anchor_count",
    "total_pool_count",
]
