"""v3.102 — clustering + AUC + geometry stability
under the +1 injected dimension.

``geometry_delta`` is the mean per-anchor
pairwise-distance change between the baseline
residual vectors and the injected vectors. A
small ``geometry_delta`` means the existing
geometry is preserved and the injection only
adds a separating axis.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_residual_vectors,
)
from ..field_leakage.distance import euclidean
from ..novel_families import all_family_members
from .inject import injected_vectors


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def all_injected_clusters() -> tuple[
    BlindCluster, ...,
]:
    vecs = injected_vectors()
    dists = pairwise_distances(vecs)
    if not dists:
        return ()
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def injected_cluster_count() -> int:
    return len(all_injected_clusters())


def injected_cluster_sizes() -> tuple[int, ...]:
    return tuple(
        len(c.members)
        for c in all_injected_clusters()
    )


def injected_purity() -> float:
    fam = _family_lookup()
    clusters = all_injected_clusters()
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            counts[fam.get(m, "?")] = (
                counts.get(fam.get(m, "?"), 0)
                + 1
            )
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total)


def injected_auc() -> float:
    fam = _family_lookup()
    vecs = injected_vectors()
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        s = -euclidean(vecs[a], vecs[b])
        if fam.get(a) == fam.get(b):
            pos.append(s)
        else:
            neg.append(s)
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return _round(
        (wins + 0.5 * ties)
        / (len(pos) * len(neg)),
    )


def geometry_delta() -> float:
    """Mean absolute change in pairwise distance
    between baseline (residual) and injected
    vectors over the C(19, 2) = 171 pairs."""
    base = entangled_residual_vectors()
    inj = injected_vectors()
    ids = sorted(base)
    deltas: list[float] = []
    for a, b in itertools.combinations(ids, 2):
        d_base = euclidean(base[a], base[b])
        d_inj = euclidean(inj[a], inj[b])
        deltas.append(abs(d_inj - d_base))
    if not deltas:
        return 0.0
    return _round(sum(deltas) / len(deltas))


def cluster_delta() -> int:
    """Difference in cluster count between
    baseline residual clustering and injected
    clustering. Negative = more clusters after
    injection."""
    base = entangled_residual_vectors()
    base_dists = pairwise_distances(base)
    base_thr = largest_gap_threshold(base_dists)
    base_clusters = single_link_cluster(
        base, base_dists, base_thr,
    )
    return injected_cluster_count() - len(
        base_clusters,
    )


__all__ = [
    "all_injected_clusters",
    "cluster_delta",
    "geometry_delta",
    "injected_auc",
    "injected_cluster_count",
    "injected_cluster_sizes",
    "injected_purity",
]
