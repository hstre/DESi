"""v3.87 — minimal-feature clustering on novel
families.

We re-use the v3.82 minimal feature set
``{branch_cost, contradiction_load}`` as the
``PROXY_DIMS`` constant and never recompute it
here. The point of this sprint is to test whether
that proxy transfers, not whether a better proxy
exists for the novel pool.
"""
from __future__ import annotations

from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..field_leakage.distance import (
    trajectory_vector,
)
from ..minimal_features.importance import (
    minimal_feature_set as v382_minimal_feature_set,
)
from ..novel_families import all_novel_anchors


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


@lru_cache(maxsize=1)
def PROXY_DIMS() -> tuple[str, ...]:
    """The v3.82 minimal feature set, frozen and
    accessed via the v3.82 module so any drift is
    surfaced immediately."""
    return tuple(sorted(v382_minimal_feature_set()))


def _dim_indices(dim_name: str) -> tuple[int, ...]:
    d = DIMENSION_NAMES.index(dim_name)
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


@lru_cache(maxsize=None)
def projected_novel_vectors(
    keep_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    keep_idx: set[int] = set()
    for d in keep_dims:
        keep_idx.update(_dim_indices(d))
    anchors = set(all_novel_anchors())
    out: dict[str, tuple[float, ...]] = {}
    for t in extract_all_trajectories():
        if t.trajectory_id not in anchors:
            continue
        v = list(trajectory_vector(t.states))
        for i in range(len(v)):
            if i not in keep_idx:
                v[i] = 0.0
        out[t.trajectory_id] = tuple(v)
    return out


@lru_cache(maxsize=None)
def cluster_novel_with(
    keep_dims: frozenset[str],
) -> tuple[BlindCluster, ...]:
    vecs = projected_novel_vectors(keep_dims)
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def cluster_with_proxy() -> tuple[BlindCluster, ...]:
    return cluster_novel_with(
        frozenset(PROXY_DIMS()),
    )


def cluster_with_full() -> tuple[BlindCluster, ...]:
    return cluster_novel_with(
        frozenset(DIMENSION_NAMES),
    )


__all__ = [
    "PROXY_DIMS",
    "cluster_novel_with",
    "cluster_with_full",
    "cluster_with_proxy",
    "projected_novel_vectors",
]
