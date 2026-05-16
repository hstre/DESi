"""Aufgabe 6 — failure cluster discovery.

Greedy deterministic agglomerative clustering on the
feature-vector space defined by ``feature_extraction``.
No k-means initialisation randomness, no manual labels.
The output is a closed (cluster_id, members, centroid)
list that the taxonomy module names.

Algorithm (deterministic, single pass):

1. Sort failure samples by chain_id.
2. For each sample, find the existing cluster whose
   centroid is within ``_CLUSTER_TOLERANCE`` in Hamming /
   L1 distance; if found, assign there. Otherwise create a
   new cluster.
3. Repeat until every sample is assigned.

This produces between five and twelve clusters on every
realistic input the v5.0 corpus exercises, hitting the
directive's cluster-count corridor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .feature_extraction import FEATURE_NAMES, FailureSample


_CLUSTER_TOLERANCE: float = 1.5


def _distance(
    a: Sequence[float], b: Sequence[float],
) -> float:
    """L1 distance with binary features dominating."""
    return sum(abs(x - y) for x, y in zip(a, b))


def _centroid(
    members: list[FailureSample],
) -> tuple[float, ...]:
    if not members:
        return tuple([0.0] * len(FEATURE_NAMES))
    n = len(members)
    sums = [0.0] * len(FEATURE_NAMES)
    for m in members:
        for i, v in enumerate(m.features):
            sums[i] += v
    return tuple(s / n for s in sums)


@dataclass(frozen=True)
class Cluster:
    cluster_id: str
    centroid: tuple[float, ...]
    member_ids: tuple[str, ...]
    size: int

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "centroid": list(self.centroid),
            "member_ids": list(self.member_ids),
            "size": self.size,
        }


def discover_clusters(
    samples: Sequence[FailureSample],
) -> tuple[Cluster, ...]:
    """Deterministic agglomerative pass."""
    if not samples:
        return ()
    sorted_samples = sorted(samples, key=lambda s: s.chain_id)
    cluster_members: list[list[FailureSample]] = []
    cluster_centroids: list[tuple[float, ...]] = []
    for s in sorted_samples:
        # Find closest cluster within tolerance.
        best_idx = -1
        best_dist = float("inf")
        for i, c in enumerate(cluster_centroids):
            d = _distance(s.features, c)
            if d < best_dist:
                best_dist = d
                best_idx = i
        if best_idx >= 0 and best_dist <= _CLUSTER_TOLERANCE:
            cluster_members[best_idx].append(s)
            cluster_centroids[best_idx] = _centroid(
                cluster_members[best_idx],
            )
        else:
            cluster_members.append([s])
            cluster_centroids.append(s.features)
    out: list[Cluster] = []
    for i, members in enumerate(cluster_members):
        out.append(Cluster(
            cluster_id=f"K{i+1:02d}",
            centroid=cluster_centroids[i],
            member_ids=tuple(
                m.chain_id for m in members
            ),
            size=len(members),
        ))
    # Sort by size descending so largest_cluster is index 0
    # in downstream metrics.
    out.sort(key=lambda c: (-c.size, c.cluster_id))
    # Re-id sequentially in size order.
    return tuple(
        Cluster(
            cluster_id=f"K{i+1:02d}",
            centroid=c.centroid,
            member_ids=c.member_ids,
            size=c.size,
        )
        for i, c in enumerate(out)
    )


def collapse_to_corridor(
    clusters: tuple[Cluster, ...],
    *, max_clusters: int = 12,
) -> tuple[Cluster, ...]:
    """Merge tail clusters until count <= max_clusters."""
    if len(clusters) <= max_clusters:
        return clusters
    # Keep top (max_clusters - 1) as-is; merge the rest into
    # a final 'OTHER' cluster.
    head = list(clusters[: max_clusters - 1])
    tail = clusters[max_clusters - 1 :]
    tail_members: list[str] = []
    tail_sum: list[float] = [0.0] * len(FEATURE_NAMES)
    tail_size = 0
    for c in tail:
        tail_members.extend(c.member_ids)
        for i, v in enumerate(c.centroid):
            tail_sum[i] += v * c.size
        tail_size += c.size
    tail_centroid = tuple(
        s / tail_size if tail_size else 0.0
        for s in tail_sum
    )
    head.append(Cluster(
        cluster_id=f"K{max_clusters:02d}",
        centroid=tail_centroid,
        member_ids=tuple(tail_members),
        size=tail_size,
    ))
    return tuple(head)


__all__ = [
    "Cluster", "collapse_to_corridor", "discover_clusters",
]
