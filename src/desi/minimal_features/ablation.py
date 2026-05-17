"""v3.82 — closed feature ablation taxonomy.

The blind clustering harness from v3.81 operates on
45-d tail vectors (5 states x 9 dimensions). An
"ablation" zeroes the 5 indices belonging to a
single dimension across all states, then reruns
the blind clustering. The directive's closed
``A/B/C/D/E/F`` set covers the four informative
dimensions plus two zero-variance controls.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..field_leakage.census import (
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    trajectory_vector,
)
from ..doppelgaenger.blind_cluster import (
    cluster_purity, cluster_recall, cluster_sizes,
    predicted_cluster_count,
)
from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..redundancy_masking.equivalence import (
    redundancy_classes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


class FeatureAblationKind(str, Enum):
    # Variance > 0 across the 20 plateau anchors:
    DROP_CONTRADICTION_LOAD = "drop_contradiction_load"
    DROP_ANCHOR_DENSITY     = "drop_anchor_density"
    DROP_NOVELTY            = "drop_novelty"
    DROP_BRANCH_COST        = "drop_branch_cost"
    # Variance == 0 (controls — ablating must not
    # change the clustering):
    DROP_FRAME_ID           = "drop_frame_id"
    DROP_SOURCE_QUALITY     = "drop_source_quality"


_ABLATION_DIM: dict[str, str] = {
    FeatureAblationKind.DROP_CONTRADICTION_LOAD.value:
        "contradiction_load",
    FeatureAblationKind.DROP_ANCHOR_DENSITY.value:
        "anchor_density",
    FeatureAblationKind.DROP_NOVELTY.value:
        "novelty",
    FeatureAblationKind.DROP_BRANCH_COST.value:
        "branch_cost",
    FeatureAblationKind.DROP_FRAME_ID.value:
        "frame_id",
    FeatureAblationKind.DROP_SOURCE_QUALITY.value:
        "source_quality",
}


def ablation_dim_name(kind: str) -> str:
    return _ABLATION_DIM[kind]


def _dim_indices(dim_name: str) -> tuple[int, ...]:
    d = DIMENSION_NAMES.index(dim_name)
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


@lru_cache(maxsize=None)
def ablated_vectors(
    drop_dims: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    """Trajectory tail vectors with every index that
    belongs to a dropped dimension zeroed out."""
    drop_idx: set[int] = set()
    for d in drop_dims:
        drop_idx.update(_dim_indices(d))
    plats = list(collect_plateau_anchors())
    out: dict[str, tuple[float, ...]] = {}
    for t in plats:
        v = list(trajectory_vector(t.states))
        for i in drop_idx:
            if 0 <= i < len(v):
                v[i] = 0.0
        out[t.trajectory_id] = tuple(v)
    return out


@lru_cache(maxsize=None)
def cluster_with_dropped(
    drop_dims: frozenset[str],
) -> tuple[BlindCluster, ...]:
    vecs = ablated_vectors(drop_dims)
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


@dataclass(frozen=True)
class AblationOutcome:
    kind: str
    dropped_dim: str
    cluster_count: int
    cluster_sizes: tuple[int, ...]
    purity: float
    recall: float

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "dropped_dim": self.dropped_dim,
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "purity": self.purity,
            "recall": self.recall,
        }


def run_one_ablation(kind: str) -> AblationOutcome:
    dim = ablation_dim_name(kind)
    clusters = cluster_with_dropped(
        frozenset({dim}),
    )
    classes = redundancy_classes()
    return AblationOutcome(
        kind=kind,
        dropped_dim=dim,
        cluster_count=predicted_cluster_count(
            clusters,
        ),
        cluster_sizes=cluster_sizes(clusters),
        purity=cluster_purity(clusters, classes),
        recall=cluster_recall(clusters, classes),
    )


@lru_cache(maxsize=1)
def all_ablation_outcomes(
) -> tuple[AblationOutcome, ...]:
    return tuple(
        run_one_ablation(k.value)
        for k in FeatureAblationKind
    )


__all__ = [
    "AblationOutcome", "FeatureAblationKind",
    "ablated_vectors", "ablation_dim_name",
    "all_ablation_outcomes",
    "cluster_with_dropped",
    "run_one_ablation",
]
