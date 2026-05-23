"""v3.82 — feature importance and minimal-set search.

* ``feature_importance``: per-dimension drop in
  cluster purity when that dimension is ablated.
* ``minimal_feature_set``: smallest subset of
  dimensions that still recovers the baseline
  clustering (greedy backward elimination ordered
  by ascending importance).
* ``proxy_score``:
  ``minimal_cluster_accuracy / baseline_accuracy``.
  1.00 means the minimal set is a perfect proxy
  for the full feature space.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.blind_cluster import (
    cluster_purity, cluster_sizes,
    predicted_cluster_count,
)
from ..doppelgaenger.equivalence import (
    all_blind_clusters,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..redundancy_masking.equivalence import (
    redundancy_classes,
)
from .ablation import (
    all_ablation_outcomes,
    cluster_with_dropped,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def baseline_purity() -> float:
    return cluster_purity(
        all_blind_clusters(), redundancy_classes(),
    )


@dataclass(frozen=True)
class FeatureImportance:
    dim: str
    baseline_purity: float
    ablated_purity: float
    importance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dim": self.dim,
            "baseline_purity": self.baseline_purity,
            "ablated_purity": self.ablated_purity,
            "importance": self.importance,
        }


@lru_cache(maxsize=1)
def feature_importance() -> tuple[
    FeatureImportance, ...,
]:
    base = baseline_purity()
    outcomes = all_ablation_outcomes()
    out: list[FeatureImportance] = []
    for o in outcomes:
        imp = _round(base - o.purity)
        out.append(FeatureImportance(
            dim=o.dropped_dim,
            baseline_purity=base,
            ablated_purity=o.purity,
            importance=imp,
        ))
    # Sort descending by importance, then by dim
    # name for determinism.
    return tuple(sorted(
        out,
        key=lambda f: (-f.importance, f.dim),
    ))


@lru_cache(maxsize=1)
def minimal_feature_set() -> tuple[str, ...]:
    """Greedy backward elimination across the full
    9-dim space. Dims outside the closed ablation
    enum are tried first (implicit importance 0);
    enum'd dims are then tried in ascending
    measured-importance order. A drop is kept only
    if cluster purity stays at baseline."""
    base = baseline_purity()
    classes = redundancy_classes()
    imps = feature_importance()
    enum_dims = {f.dim for f in imps}
    # Implicit-zero-importance dims first, then
    # enum'd dims in ascending importance.
    order: list[str] = sorted(
        d for d in DIMENSION_NAMES
        if d not in enum_dims
    )
    order.extend(
        f.dim for f in reversed(imps)
    )
    kept = set(DIMENSION_NAMES)
    dropped: set[str] = set()
    for dim in order:
        trial = dropped | {dim}
        clusters = cluster_with_dropped(
            frozenset(trial),
        )
        if cluster_purity(
            clusters, classes,
        ) >= base:
            dropped = trial
            kept.discard(dim)
    return tuple(sorted(kept))


def minimal_cluster_accuracy() -> float:
    minimal = set(minimal_feature_set())
    drop = frozenset(
        d for d in DIMENSION_NAMES
        if d not in minimal
    )
    clusters = cluster_with_dropped(drop)
    return cluster_purity(
        clusters, redundancy_classes(),
    )


def proxy_score() -> float:
    base = baseline_purity()
    if base == 0.0:
        return 0.0
    return _round(minimal_cluster_accuracy() / base)


__all__ = [
    "FeatureImportance",
    "baseline_purity",
    "feature_importance",
    "minimal_cluster_accuracy",
    "minimal_feature_set",
    "proxy_score",
]
