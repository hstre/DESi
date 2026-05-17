"""v3.96 — resolution metrics over the augmented
feature space.

For every candidate FeatureSpec we compute:

* cluster purity (single-link / largest-gap),
* pairwise AUC (score = -euclidean),
* FPR at the optimal-margin threshold.

A closed search enumerates spec sizes up to a
fixed cap; the best spec is the one that maximises
purity, then AUC, then prefers smaller size.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from ..field_leakage.distance import euclidean
from ..frame_normalized_predictive.forecast import (
    frame_normalized_auc, frame_normalized_fpr,
    optimal_threshold as fn_optimal_threshold,
)
from ..novel_families import all_family_members
from .resolve import (
    FeatureSpec, RESIDUAL_DIMS, TEMPORAL_DIMS,
    feature_vector_for_spec,
)


MAX_SEARCH_SIZE: int = 3


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def cluster_for(
    spec: FeatureSpec,
) -> tuple[BlindCluster, ...]:
    vecs = feature_vector_for_spec(spec)
    dists = pairwise_distances(vecs)
    if not dists:
        return ()
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


def purity_for(spec: FeatureSpec) -> float:
    lookup = _family_lookup()
    clusters = cluster_for(spec)
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


def auc_for(spec: FeatureSpec) -> float:
    fam = _family_lookup()
    vecs = feature_vector_for_spec(spec)
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


def fpr_for(spec: FeatureSpec) -> float:
    """FPR at the optimal-margin threshold for the
    spec's distance-based score."""
    fam = _family_lookup()
    vecs = feature_vector_for_spec(spec)
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
        return 0.0
    thr = (min(pos) + max(neg)) / 2.0
    fp = sum(1 for s in neg if s >= thr)
    return _round(fp / len(neg))


@dataclass(frozen=True)
class ResolutionOutcome:
    spec: FeatureSpec
    cluster_count: int
    cluster_sizes: tuple[int, ...]
    purity: float
    auc: float
    fpr: float

    def to_dict(self) -> dict[str, object]:
        return {
            "spec": self.spec.to_dict(),
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "purity": self.purity,
            "auc": self.auc,
            "fpr": self.fpr,
        }


def _enumerate_specs() -> tuple[FeatureSpec, ...]:
    """Closed search over:

    * residual-only subsets (size 1..MAX),
    * temporal-only subsets (size 1..MAX),
    * combined subsets (1 residual + 1 temporal,
      and the full residual + 1 temporal pair).
    """
    out: list[FeatureSpec] = []
    for k in range(1, MAX_SEARCH_SIZE + 1):
        for combo in itertools.combinations(
            RESIDUAL_DIMS, k,
        ):
            out.append(FeatureSpec(
                residual_dims=tuple(sorted(combo)),
                temporal_dims=(),
            ))
        for combo in itertools.combinations(
            TEMPORAL_DIMS, k,
        ):
            out.append(FeatureSpec(
                residual_dims=(),
                temporal_dims=tuple(sorted(combo)),
            ))
    # Cross combinations: every (1 residual + 1
    # temporal).
    for r in RESIDUAL_DIMS:
        for t in TEMPORAL_DIMS:
            out.append(FeatureSpec(
                residual_dims=(r,),
                temporal_dims=(t,),
            ))
    # Full residual + each temporal singleton.
    for t in TEMPORAL_DIMS:
        out.append(FeatureSpec(
            residual_dims=tuple(RESIDUAL_DIMS),
            temporal_dims=(t,),
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def all_resolution_outcomes() -> tuple[
    ResolutionOutcome, ...,
]:
    out: list[ResolutionOutcome] = []
    for spec in _enumerate_specs():
        clusters = cluster_for(spec)
        out.append(ResolutionOutcome(
            spec=spec,
            cluster_count=len(clusters),
            cluster_sizes=tuple(
                len(c.members) for c in clusters
            ),
            purity=purity_for(spec),
            auc=auc_for(spec),
            fpr=fpr_for(spec),
        ))
    return tuple(out)


def best_outcome() -> ResolutionOutcome:
    outs = all_resolution_outcomes()
    return max(
        outs,
        key=lambda o: (
            o.purity, o.auc, -o.spec.size,
            tuple(sorted(o.spec.residual_dims)),
            tuple(sorted(o.spec.temporal_dims)),
        ),
    )


def best_feature_set() -> FeatureSpec:
    return best_outcome().spec


def resolved_purity() -> float:
    return best_outcome().purity


def resolved_auc() -> float:
    return best_outcome().auc


def resolved_fpr() -> float:
    return best_outcome().fpr


def baseline_frame_normalized_auc() -> float:
    return frame_normalized_auc()


def baseline_frame_normalized_fpr() -> float:
    return frame_normalized_fpr(
        fn_optimal_threshold(),
    )


__all__ = [
    "MAX_SEARCH_SIZE",
    "ResolutionOutcome",
    "all_resolution_outcomes",
    "auc_for",
    "baseline_frame_normalized_auc",
    "baseline_frame_normalized_fpr",
    "best_feature_set", "best_outcome",
    "cluster_for", "fpr_for",
    "purity_for", "resolved_auc",
    "resolved_fpr", "resolved_purity",
]
