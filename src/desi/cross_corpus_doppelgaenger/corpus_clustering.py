"""v3.83 — per-corpus + joint blind clustering.

Reuses the v3.81 largest-gap single-link primitive
on each of the four closed reference corpora
(v2.3, v3.14, v3.15, v3.16) and on their union.
Single-anchor corpora are clustered trivially as
one cluster.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..cross_corpus.corpus_loader import (
    CorpusKind, corpus_plateau_anchors,
)
from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    single_link_cluster,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _build_vecs(
    anchors,
) -> dict[str, tuple[float, ...]]:
    return {
        a.trajectory_id: trajectory_vector(a.states)
        for a in anchors
    }


def _pairwise(
    vecs: dict[str, tuple[float, ...]],
) -> tuple[tuple[str, str, float], ...]:
    ids = sorted(vecs)
    return tuple(
        (a, b, _round(euclidean(vecs[a], vecs[b])))
        for a, b in itertools.combinations(ids, 2)
    )


@lru_cache(maxsize=None)
def corpus_clusters(
    corpus: str,
) -> tuple[BlindCluster, ...]:
    anchors = corpus_plateau_anchors(corpus)
    if not anchors:
        return ()
    vecs = _build_vecs(anchors)
    if len(vecs) == 1:
        only_id = next(iter(vecs))
        return (
            BlindCluster(
                cluster_id=0,
                members=(only_id,),
                mean_intra_distance=0.0,
                max_intra_distance=0.0,
            ),
        )
    dists = _pairwise(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


@lru_cache(maxsize=1)
def joint_anchors():
    out = []
    for k in CorpusKind:
        out.extend(corpus_plateau_anchors(k.value))
    return tuple(out)


@lru_cache(maxsize=1)
def joint_clusters() -> tuple[BlindCluster, ...]:
    anchors = joint_anchors()
    if not anchors:
        return ()
    vecs = _build_vecs(anchors)
    if len(vecs) == 1:
        only_id = next(iter(vecs))
        return (
            BlindCluster(
                cluster_id=0,
                members=(only_id,),
                mean_intra_distance=0.0,
                max_intra_distance=0.0,
            ),
        )
    dists = _pairwise(vecs)
    thr = largest_gap_threshold(dists)
    return single_link_cluster(vecs, dists, thr)


@dataclass(frozen=True)
class CorpusClusterSummary:
    corpus: str
    anchor_count: int
    cluster_count: int
    cluster_sizes: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus": self.corpus,
            "anchor_count": self.anchor_count,
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
        }


def per_corpus_summaries() -> tuple[
    CorpusClusterSummary, ...,
]:
    out: list[CorpusClusterSummary] = []
    for k in CorpusKind:
        clusters = corpus_clusters(k.value)
        anchors = corpus_plateau_anchors(k.value)
        out.append(CorpusClusterSummary(
            corpus=k.value,
            anchor_count=len(anchors),
            cluster_count=len(clusters),
            cluster_sizes=tuple(
                len(c.members) for c in clusters
            ),
        ))
    return tuple(out)


def intra_corpus_classes() -> tuple[int, ...]:
    return tuple(
        s.cluster_count for s in per_corpus_summaries()
    )


__all__ = [
    "CorpusClusterSummary",
    "corpus_clusters",
    "intra_corpus_classes",
    "joint_anchors", "joint_clusters",
    "per_corpus_summaries",
]
