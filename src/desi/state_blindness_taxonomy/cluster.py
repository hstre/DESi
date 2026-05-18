"""v3.118 — per-pool classification and
aggregate rates."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)
from .taxonomy import (
    BlindnessKind, _mean_pairwise_jaccard,
    classify_pool,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ClassifiedPool:
    pool_id: int
    kind: str
    member_count: int
    family_count: int
    mean_text_jaccard: float

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "kind": self.kind,
            "member_count": self.member_count,
            "family_count": self.family_count,
            "mean_text_jaccard":
                self.mean_text_jaccard,
        }


@lru_cache(maxsize=1)
def all_classified_pools() -> tuple[
    ClassifiedPool, ...,
]:
    out: list[ClassifiedPool] = []
    for p in cross_family_pools():
        kind = classify_pool(p)
        out.append(ClassifiedPool(
            pool_id=p.pool_id,
            kind=kind,
            member_count=p.member_count,
            family_count=p.family_count,
            mean_text_jaccard=(
                _mean_pairwise_jaccard(
                    p.member_ids,
                )
            ),
        ))
    return tuple(out)


def taxonomy_counts() -> dict[str, int]:
    out = {k.value: 0 for k in BlindnessKind}
    for p in all_classified_pools():
        out[p.kind] = out.get(p.kind, 0) + 1
    return out


def duplicate_rate() -> float:
    pools = all_classified_pools()
    if not pools:
        return 0.0
    n = sum(
        1 for p in pools
        if p.kind == (
            BlindnessKind.DUPLICATE_COLLAPSE.value
        )
    )
    return _round(n / len(pools))


def semantic_blindness_rate() -> float:
    pools = all_classified_pools()
    if not pools:
        return 0.0
    n = sum(
        1 for p in pools
        if p.kind == (
            BlindnessKind.SEMANTIC_COLLAPSE.value
        )
    )
    return _round(n / len(pools))


def structural_rate() -> float:
    pools = all_classified_pools()
    if not pools:
        return 0.0
    n = sum(
        1 for p in pools
        if p.kind == (
            BlindnessKind.STRUCTURAL_COLLAPSE.value
        )
    )
    return _round(n / len(pools))


def routing_rate() -> float:
    pools = all_classified_pools()
    if not pools:
        return 0.0
    n = sum(
        1 for p in pools
        if p.kind == (
            BlindnessKind.ROUTING_COLLAPSE.value
        )
    )
    return _round(n / len(pools))


def unknown_rate() -> float:
    pools = all_classified_pools()
    if not pools:
        return 0.0
    n = sum(
        1 for p in pools
        if p.kind == BlindnessKind.UNKNOWN.value
    )
    return _round(n / len(pools))


__all__ = [
    "ClassifiedPool",
    "all_classified_pools",
    "duplicate_rate",
    "routing_rate",
    "semantic_blindness_rate",
    "structural_rate",
    "taxonomy_counts",
    "unknown_rate",
]
