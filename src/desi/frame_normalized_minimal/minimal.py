"""v3.91 — minimal-feature projections over the
frame-normalized novel anchor pool.

We test four conditions per the directive:

* ``PROXY_ONLY``     - {branch_cost,
  contradiction_load} on the v3.89 residual
  vectors.
* ``PROXY_PLUS_X``   - the proxy plus each
  individual non-frame, non-proxy dimension
  (residual space).
* ``NO_FRAME``       - frame_id zeroed but no
  per-cell regression.
* ``RESIDUAL``       - the v3.89 residual
  projection (frame_id zeroed AND regressed out).
"""
from __future__ import annotations

from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..frame_normalization.contribution import (
    novel_vectors_no_frame,
    novel_vectors_residual,
)
from ..novel_minimal_features.minimal import (
    PROXY_DIMS,
)


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


def _dim_indices(dim_name: str) -> tuple[int, ...]:
    d = DIMENSION_NAMES.index(dim_name)
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


def _project(
    base: dict[str, tuple[float, ...]],
    keep_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    keep_idx: set[int] = set()
    for d in keep_dims:
        keep_idx.update(_dim_indices(d))
    out: dict[str, tuple[float, ...]] = {}
    for tid, v in base.items():
        w = [
            x if i in keep_idx else 0.0
            for i, x in enumerate(v)
        ]
        out[tid] = tuple(w)
    return out


@lru_cache(maxsize=None)
def residual_projection(
    keep_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    return _project(
        novel_vectors_residual(), keep_dims,
    )


@lru_cache(maxsize=None)
def no_frame_projection(
    keep_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    return _project(
        novel_vectors_no_frame(), keep_dims,
    )


@lru_cache(maxsize=None)
def cluster_residual(
    keep_dims: frozenset[str],
) -> tuple[BlindCluster, ...]:
    vecs = residual_projection(keep_dims)
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def residual_full() -> dict[
    str, tuple[float, ...],
]:
    return novel_vectors_residual()


__all__ = [
    "PROXY_DIMS",
    "cluster_residual",
    "no_frame_projection",
    "residual_full",
    "residual_projection",
]
