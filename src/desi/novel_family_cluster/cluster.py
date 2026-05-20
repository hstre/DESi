"""v3.86 — blind doppelganger clustering on novel
families.

Same algorithm as v3.81: single-link agglomeration
on the 45-d tail-vector matrix using the largest-
gap midpoint threshold. No family_id, no class id,
no coverage feedback influences the partition.
Family labels are consulted only at metric-readout
time (purity, recall).
"""
from __future__ import annotations

from ..doppelgaenger.equivalence import (
    BlindCluster, single_link_cluster,
)
from ..novel_families import (
    NovelFamily, all_family_members,
    all_novel_families,
)
from .distance import (
    novel_anchor_vectors,
    novel_distance_gap,
    novel_pairwise_distances,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def all_novel_blind_clusters() -> tuple[
    BlindCluster, ...,
]:
    vecs = novel_anchor_vectors()
    dists = novel_pairwise_distances()
    threshold = novel_distance_gap()
    return single_link_cluster(vecs, dists, threshold)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def cluster_purity(
    clusters: tuple[BlindCluster, ...],
) -> float:
    """Weighted majority purity over family ids."""
    lookup = _family_lookup()
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            fid = lookup.get(m, "?")
            counts[fid] = counts.get(fid, 0) + 1
        correct += max(counts.values()) if counts else 0
    return _round(correct / total)


def cluster_recall(
    clusters: tuple[BlindCluster, ...],
) -> float:
    """Fraction of families that appear as exactly
    one blind cluster (every member of the family
    ends up in the same cluster AND that cluster
    contains only members of that family)."""
    families = all_novel_families()
    if not families:
        return 0.0
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


def predicted_cluster_count(
    clusters: tuple[BlindCluster, ...],
) -> int:
    return len(clusters)


def cluster_sizes(
    clusters: tuple[BlindCluster, ...],
) -> tuple[int, ...]:
    return tuple(len(c.members) for c in clusters)


__all__ = [
    "all_novel_blind_clusters",
    "cluster_purity", "cluster_recall",
    "cluster_sizes",
    "predicted_cluster_count",
]
