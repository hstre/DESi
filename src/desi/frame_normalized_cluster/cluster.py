"""v3.90 — blind clustering on frame-normalized
novel anchors.

Reuses the v3.81 single-link/largest-gap algorithm.
Input vectors come from the v3.90 normalization
adapter, so the algorithm itself is untouched.
"""
from __future__ import annotations

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..novel_families import (
    NovelFamily, all_family_members,
    all_novel_families,
)
from .normalize import frame_normalized_vectors


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def normalized_pairwise_distances() -> tuple[
    tuple[str, str, float], ...,
]:
    return pairwise_distances(
        frame_normalized_vectors(),
    )


def normalized_distance_gap() -> float:
    return largest_gap_threshold(
        normalized_pairwise_distances(),
    )


def all_normalized_clusters() -> tuple[
    BlindCluster, ...,
]:
    vecs = frame_normalized_vectors()
    dists = normalized_pairwise_distances()
    return single_link_cluster(
        vecs, dists,
        normalized_distance_gap(),
    )


def normalized_cluster_count() -> int:
    return len(all_normalized_clusters())


def normalized_cluster_sizes() -> tuple[int, ...]:
    return tuple(
        len(c.members)
        for c in all_normalized_clusters()
    )


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def normalized_cluster_purity() -> float:
    lookup = _family_lookup()
    clusters = all_normalized_clusters()
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            counts[lookup.get(m, "?")] = (
                counts.get(lookup.get(m, "?"), 0)
                + 1
            )
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total)


def normalized_cluster_recall() -> float:
    families = all_novel_families()
    if not families:
        return 0.0
    clusters = all_normalized_clusters()
    member_to_cluster: dict[str, int] = {}
    cluster_lookup: dict[int, BlindCluster] = {}
    for cl in clusters:
        cluster_lookup[cl.cluster_id] = cl
        for m in cl.members:
            member_to_cluster[m] = cl.cluster_id
    recovered = 0
    for fam in families:
        if not fam.members:
            continue
        ids = {
            member_to_cluster.get(m, -1)
            for m in fam.members
        }
        if len(ids) != 1:
            continue
        only = next(iter(ids))
        if only == -1:
            continue
        bc = cluster_lookup[only]
        if set(bc.members) == set(fam.members):
            recovered += 1
    return _round(recovered / len(families))


__all__ = [
    "all_normalized_clusters",
    "normalized_cluster_count",
    "normalized_cluster_purity",
    "normalized_cluster_recall",
    "normalized_cluster_sizes",
    "normalized_distance_gap",
    "normalized_pairwise_distances",
]
