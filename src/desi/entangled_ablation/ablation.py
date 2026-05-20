"""v3.94 — feature-subset ablation on the
entangled (G_v316susp + E_v317h) residual subspace.

For every dim subset of size 1..K we project the
v3.89 residual vectors and run the v3.81 single-
link / largest-gap clustering. Purity is read off
the v3.85 family map.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
    entangled_residual_vectors,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..novel_families import all_family_members


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _dim_indices(dim_name: str) -> tuple[int, ...]:
    d = DIMENSION_NAMES.index(dim_name)
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


@lru_cache(maxsize=None)
def projected_entangled_vectors(
    keep_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    keep_idx: set[int] = set()
    for d in keep_dims:
        keep_idx.update(_dim_indices(d))
    vecs = entangled_residual_vectors()
    out: dict[str, tuple[float, ...]] = {}
    for tid, v in vecs.items():
        w = [
            x if i in keep_idx else 0.0
            for i, x in enumerate(v)
        ]
        out[tid] = tuple(w)
    return out


@lru_cache(maxsize=None)
def cluster_entangled_with(
    keep_dims: frozenset[str],
) -> tuple[BlindCluster, ...]:
    vecs = projected_entangled_vectors(keep_dims)
    dists = pairwise_distances(vecs)
    if not dists:
        return ()
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def cluster_purity(
    clusters: tuple[BlindCluster, ...],
) -> float:
    lookup = _family_lookup()
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


def baseline_purity() -> float:
    """Majority-class purity for the entangled pair
    (= |E| / (|G| + |E|))."""
    fams = all_family_members()
    sizes = [
        len(fams.get(fid, ()))
        for fid in ENTANGLED_FAMILY_IDS
    ]
    total = sum(sizes)
    return _round(max(sizes) / total) if total else 0.0


@dataclass(frozen=True)
class AblationOutcome:
    dims: tuple[str, ...]
    dim_count: int
    cluster_count: int
    cluster_sizes: tuple[int, ...]
    purity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dims": list(self.dims),
            "dim_count": self.dim_count,
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "purity": self.purity,
        }


__all__ = [
    "AblationOutcome",
    "baseline_purity",
    "cluster_entangled_with",
    "cluster_purity",
    "projected_entangled_vectors",
]
