"""v3.81 — blind cluster quality metrics.

Compares the v3.81 blind clustering against the
v3.79 redundancy class map (the ground truth).
Purity, recall and class match are read out without
feeding the labels back into the clustering itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..redundancy_masking.equivalence import (
    RedundancyClass, redundancy_classes,
)
from .equivalence import (
    BlindCluster, all_blind_clusters,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def predicted_cluster_count(
    clusters: tuple[BlindCluster, ...],
) -> int:
    return len(clusters)


def cluster_sizes(
    clusters: tuple[BlindCluster, ...],
) -> tuple[int, ...]:
    return tuple(
        len(c.members) for c in clusters
    )


def _class_lookup(
    classes: tuple[RedundancyClass, ...],
) -> dict[str, int]:
    return {
        m: c.class_id
        for c in classes for m in c.members
    }


def cluster_purity(
    clusters: tuple[BlindCluster, ...],
    classes: tuple[RedundancyClass, ...],
) -> float:
    """Weighted majority purity: for each cluster,
    count members of the most frequent true class,
    sum over clusters, divide by total members."""
    lookup = _class_lookup(classes)
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        if not c.members:
            continue
        counts: dict[int, int] = {}
        for m in c.members:
            cid = lookup.get(m, -1)
            counts[cid] = counts.get(cid, 0) + 1
        correct += max(counts.values())
    return _round(correct / total)


def cluster_recall(
    clusters: tuple[BlindCluster, ...],
    classes: tuple[RedundancyClass, ...],
) -> float:
    """Fraction of true classes that appear as a
    single blind cluster (= every member of the
    true class ends up in the same blind cluster,
    AND that blind cluster has no other-class
    members)."""
    if not classes:
        return 0.0
    member_to_cluster: dict[str, int] = {}
    for cl in clusters:
        for m in cl.members:
            member_to_cluster[m] = cl.cluster_id
    cluster_lookup = {
        c.cluster_id: c for c in clusters
    }
    recovered = 0
    for cls in classes:
        if not cls.members:
            continue
        ids = {
            member_to_cluster.get(m, -1)
            for m in cls.members
        }
        if len(ids) != 1:
            continue
        only = next(iter(ids))
        if only == -1:
            continue
        bc = cluster_lookup[only]
        if set(bc.members) == set(cls.members):
            recovered += 1
    return _round(recovered / len(classes))


@dataclass(frozen=True)
class ClusterClassMatch:
    cluster_id: int
    matched_class_id: int
    member_overlap: int
    is_exact: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "matched_class_id":
                self.matched_class_id,
            "member_overlap": self.member_overlap,
            "is_exact": self.is_exact,
        }


def cluster_class_matches(
    clusters: tuple[BlindCluster, ...],
    classes: tuple[RedundancyClass, ...],
) -> tuple[ClusterClassMatch, ...]:
    out: list[ClusterClassMatch] = []
    for cl in clusters:
        best_id = -1
        best_overlap = 0
        for cls in classes:
            overlap = len(
                set(cl.members) & set(cls.members)
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_id = cls.class_id
        matched_set = (
            set(
                next(
                    c for c in classes
                    if c.class_id == best_id
                ).members,
            )
            if best_id != -1 else set()
        )
        exact = (
            best_id != -1
            and set(cl.members) == matched_set
        )
        out.append(ClusterClassMatch(
            cluster_id=cl.cluster_id,
            matched_class_id=best_id,
            member_overlap=best_overlap,
            is_exact=exact,
        ))
    return tuple(out)


def all_blind_metrics() -> dict[str, object]:
    clusters = all_blind_clusters()
    classes = redundancy_classes()
    return {
        "predicted_cluster_count":
            predicted_cluster_count(clusters),
        "cluster_sizes":
            list(cluster_sizes(clusters)),
        "cluster_purity":
            cluster_purity(clusters, classes),
        "cluster_recall":
            cluster_recall(clusters, classes),
    }


__all__ = [
    "ClusterClassMatch",
    "all_blind_metrics",
    "cluster_class_matches",
    "cluster_purity",
    "cluster_recall",
    "cluster_sizes",
    "predicted_cluster_count",
]
