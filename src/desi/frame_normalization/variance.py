"""v3.89 — per-condition cluster purity.

For each ``FrameCondition`` (FULL, NO_FRAME,
FRAME_ONLY, RESIDUAL) we run the v3.81 single-link
clustering on the projected/residual vectors and
read the family-purity off the v3.85 family map.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..novel_families import all_family_members
from .contribution import (
    FrameCondition, vectors_for_condition,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=None)
def cluster_for_condition(
    condition: str,
) -> tuple[BlindCluster, ...]:
    vecs = vectors_for_condition(condition)
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def cluster_purity_for(
    condition: str,
) -> float:
    lookup = _family_lookup()
    clusters = cluster_for_condition(condition)
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            fid = lookup.get(m, "?")
            counts[fid] = counts.get(fid, 0) + 1
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total)


def cluster_count_for(condition: str) -> int:
    return len(cluster_for_condition(condition))


def cluster_sizes_for(
    condition: str,
) -> tuple[int, ...]:
    return tuple(
        len(c.members)
        for c in cluster_for_condition(condition)
    )


@dataclass(frozen=True)
class ConditionOutcome:
    condition: str
    cluster_count: int
    cluster_sizes: tuple[int, ...]
    purity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "condition": self.condition,
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "purity": self.purity,
        }


def all_condition_outcomes() -> tuple[
    ConditionOutcome, ...,
]:
    return tuple(
        ConditionOutcome(
            condition=c.value,
            cluster_count=cluster_count_for(c.value),
            cluster_sizes=cluster_sizes_for(c.value),
            purity=cluster_purity_for(c.value),
        )
        for c in FrameCondition
    )


__all__ = [
    "ConditionOutcome",
    "all_condition_outcomes",
    "cluster_count_for",
    "cluster_for_condition",
    "cluster_purity_for",
    "cluster_sizes_for",
]
