"""v3.81 — blind equivalence primitives.

DESi sees only plateau anchor trajectories. No
coverage labels, no class identities, no ablation
oracle. Blindly partition the anchors into clusters
of "indistinguishable behaviour" using a gap-based
threshold on the pairwise tail-vector distance
matrix.

The threshold is chosen as the midpoint of the
largest gap in the sorted pairwise-distance list -
the data picks its own scale, no peeking at the
v3.79 redundancy class map.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from ..field_leakage.census import (
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def plateau_anchor_vectors(
) -> dict[str, tuple[float, ...]]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    }


def pairwise_distances(
    vecs: dict[str, tuple[float, ...]],
) -> tuple[tuple[str, str, float], ...]:
    ids = sorted(vecs)
    return tuple(
        (a, b, _round(euclidean(vecs[a], vecs[b])))
        for a, b in itertools.combinations(ids, 2)
    )


def largest_gap_threshold(
    distances: tuple[tuple[str, str, float], ...],
) -> float:
    """Midpoint of the single largest jump in the
    sorted pairwise-distance list. If only one
    distinct distance exists, return slightly above
    it so all items collapse to one cluster."""
    if not distances:
        return 0.0
    ds = sorted(d for _, _, d in distances)
    if len(ds) == 1:
        return _round(ds[0] + 1.0)
    best_gap = -1.0
    best_mid = ds[-1] + 1.0
    for i in range(len(ds) - 1):
        gap = ds[i + 1] - ds[i]
        if gap > best_gap:
            best_gap = gap
            best_mid = (ds[i] + ds[i + 1]) / 2.0
    return _round(best_mid)


@dataclass(frozen=True)
class BlindCluster:
    cluster_id: int
    members: tuple[str, ...]
    mean_intra_distance: float
    max_intra_distance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "members": list(self.members),
            "mean_intra_distance":
                self.mean_intra_distance,
            "max_intra_distance":
                self.max_intra_distance,
        }


def _union_find(
    ids: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> dict[str, str]:
    parent = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            # Union by lexicographic minimum so the
            # root is deterministic.
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb
    return {i: find(i) for i in ids}


def single_link_cluster(
    vecs: dict[str, tuple[float, ...]],
    distances: tuple[tuple[str, str, float], ...],
    threshold: float,
) -> tuple[BlindCluster, ...]:
    ids = tuple(sorted(vecs))
    edges = tuple(
        (a, b) for a, b, d in distances
        if d <= threshold
    )
    roots = _union_find(ids, edges)
    by_root: dict[str, list[str]] = {}
    for member, root in roots.items():
        by_root.setdefault(root, []).append(member)
    groups = sorted(
        by_root.values(),
        key=lambda m: (-len(m), m[0]),
    )
    dmap = {
        (a, b): d for a, b, d in distances
    }
    out: list[BlindCluster] = []
    for i, members in enumerate(groups):
        ms = tuple(sorted(members))
        intra = []
        for a, b in itertools.combinations(ms, 2):
            key = (a, b) if (a, b) in dmap else (b, a)
            intra.append(dmap.get(key, 0.0))
        mean_d = (
            _round(sum(intra) / len(intra))
            if intra else 0.0
        )
        max_d = (
            _round(max(intra)) if intra else 0.0
        )
        out.append(BlindCluster(
            cluster_id=i,
            members=ms,
            mean_intra_distance=mean_d,
            max_intra_distance=max_d,
        ))
    return tuple(out)


def all_blind_clusters() -> tuple[
    BlindCluster, ...,
]:
    vecs = plateau_anchor_vectors()
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


__all__ = [
    "BlindCluster",
    "all_blind_clusters",
    "largest_gap_threshold",
    "pairwise_distances",
    "plateau_anchor_vectors",
    "single_link_cluster",
]
