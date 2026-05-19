"""v15.2 - blindness pools (structural clusters).

A blindness pool is a set of firms whose structural
signatures sit within a fixed radius of one another
- firms an auditor would tend to misread the same
way. Pools are built by deterministic single-
linkage on the signature distance, so the grouping
is reproducible and depends only on EPISTEMIC
STRUCTURE, never on the sector label.

Reads no post-hoc label.
"""
from __future__ import annotations

from dataclasses import dataclass

from .trajectory_similarity import (
    distance, signature, signatures,
)

# Single-linkage merge radius (normalised distance).
_TAU = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _pool_ids() -> list[list[str]]:
    ids = [sig.firm_id for sig in signatures()]
    # union-find over the distance graph
    parent = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            # keep the lexicographically smaller
            # root for deterministic labels
            lo, hi = sorted((ra, rb))
            parent[hi] = lo

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if distance(a, b) <= _TAU:
                union(a, b)

    groups: dict[str, list[str]] = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    pools = [sorted(g) for g in groups.values()]
    pools.sort(key=lambda g: (g[0],))
    return pools


@dataclass(frozen=True)
class BlindnessPool:
    pool_id: int
    members: tuple[str, ...]
    sectors: tuple[str, ...]
    centroid: tuple[float, ...]

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def is_cross_sector(self) -> bool:
        return len(set(self.sectors)) > 1

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "members": list(self.members),
            "sectors": list(self.sectors),
            "size": self.size,
            "is_cross_sector": self.is_cross_sector,
            "centroid": [
                round(v, 6) for v in self.centroid
            ],
        }


def _centroid(members: list[str]) -> tuple[float, ...]:
    vecs = [signature(m).values for m in members]
    dim = len(vecs[0])
    return tuple(
        _round(
            sum(v[i] for v in vecs) / len(vecs),
        )
        for i in range(dim)
    )


def pools() -> tuple[BlindnessPool, ...]:
    out: list[BlindnessPool] = []
    for idx, members in enumerate(_pool_ids()):
        sectors = tuple(
            signature(m).sector for m in members
        )
        out.append(BlindnessPool(
            pool_id=idx,
            members=tuple(members),
            sectors=sectors,
            centroid=_centroid(members),
        ))
    return tuple(out)


def blindness_pool_count() -> int:
    return len(pools())


def pool_of(firm_id: str) -> BlindnessPool:
    for p in pools():
        if firm_id in p.members:
            return p
    raise KeyError(firm_id)


def multi_member_pools() -> tuple[BlindnessPool, ...]:
    return tuple(p for p in pools() if p.size > 1)


__all__ = [
    "BlindnessPool",
    "blindness_pool_count",
    "multi_member_pools",
    "pool_of",
    "pools",
]
