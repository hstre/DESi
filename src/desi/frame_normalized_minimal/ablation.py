"""v3.91 — feature ablation and minimal-set search
on frame-normalized novel anchors.

* ``normalized_proxy_accuracy`` - cluster purity of
  {branch_cost, contradiction_load} on residual
  vectors.
* ``normalized_predictive_auc`` - pairwise ROC AUC
  on the full residual feature space (the
  directive's "frame-normalized features"
  condition for prediction).
* ``best_minimal_feature_set`` - smallest feature
  subset (residual space) whose cluster purity
  equals or exceeds the proxy purity.
* ``marginal_frame_gain`` - residual full-feature
  purity minus pre-normalization full purity, i.e.
  the boost attributable to frame removal alone.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    pairwise_distances,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..field_leakage.distance import (
    euclidean,
)
from ..frame_normalization.contribution import (
    novel_vectors_full,
    novel_vectors_no_frame,
    novel_vectors_residual,
)
from ..novel_families import all_family_members
from ..novel_family_cluster.cluster import (
    cluster_purity as novel_full_purity,
    all_novel_blind_clusters,
)
from .minimal import (
    PROXY_DIMS, cluster_residual,
    residual_projection, residual_full,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def _purity(clusters) -> float:
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


def normalized_proxy_accuracy() -> float:
    return _purity(
        cluster_residual(frozenset(PROXY_DIMS())),
    )


def _pairwise_auc(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _family_lookup()
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        score = -euclidean(vecs[a], vecs[b])
        if fam.get(a) == fam.get(b):
            pos.append(score)
        else:
            neg.append(score)
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


def normalized_predictive_auc() -> float:
    return _pairwise_auc(residual_full())


@dataclass(frozen=True)
class FeatureSubsetOutcome:
    dims: tuple[str, ...]
    cluster_count: int
    cluster_sizes: tuple[int, ...]
    purity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dims": list(self.dims),
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "purity": self.purity,
        }


_INFORMATIVE_DIMS: tuple[str, ...] = (
    "branch_cost", "contradiction_load",
    "novelty",
)


@lru_cache(maxsize=1)
def informative_subset_outcomes() -> tuple[
    FeatureSubsetOutcome, ...,
]:
    out: list[FeatureSubsetOutcome] = []
    for k in range(1, len(_INFORMATIVE_DIMS) + 1):
        for combo in itertools.combinations(
            _INFORMATIVE_DIMS, k,
        ):
            cls = cluster_residual(frozenset(combo))
            out.append(FeatureSubsetOutcome(
                dims=tuple(sorted(combo)),
                cluster_count=len(cls),
                cluster_sizes=tuple(
                    len(c.members) for c in cls
                ),
                purity=_purity(cls),
            ))
    return tuple(out)


def best_minimal_feature_set() -> tuple[str, ...]:
    """Smallest feature subset (residual space)
    that achieves the best purity over the closed
    informative-dim taxonomy. Ties broken by
    smallest size, then by alphabetic order."""
    outcomes = informative_subset_outcomes()
    if not outcomes:
        return ()
    best = max(
        outcomes,
        key=lambda o: (
            o.purity, -len(o.dims),
            tuple(sorted(o.dims)),
        ),
    )
    # Now find the smallest set that ties best
    # purity.
    smallest = min(
        (o for o in outcomes if o.purity == best.purity),
        key=lambda o: (len(o.dims), o.dims),
    )
    return smallest.dims


def marginal_frame_gain() -> float:
    """Residual full purity minus raw full purity
    (the boost from frame normalisation alone)."""
    raw_purity = novel_full_purity(
        all_novel_blind_clusters(),
    )
    from ..doppelgaenger.equivalence import (
        largest_gap_threshold,
        single_link_cluster,
    )
    res_v = residual_full()
    res_dists = pairwise_distances(res_v)
    res_thr = largest_gap_threshold(res_dists)
    res_clusters = single_link_cluster(
        res_v, res_dists, res_thr,
    )
    res_purity = _purity(res_clusters)
    return _round(res_purity - raw_purity)


__all__ = [
    "FeatureSubsetOutcome",
    "_INFORMATIVE_DIMS",
    "best_minimal_feature_set",
    "informative_subset_outcomes",
    "marginal_frame_gain",
    "normalized_predictive_auc",
    "normalized_proxy_accuracy",
]
