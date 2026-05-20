"""v3.32 — plateau clustering.

Deterministic single-pass agglomerative clustering over
plateau feature vectors. Same shape as the v5.0
methodology-transfer clusterer: sort samples by id,
assign each to the nearest existing cluster within an
L1 tolerance, else open a new cluster.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .plateau_signals import PlateauFeatures


_CLUSTER_TOLERANCE: float = 2.0


@dataclass(frozen=True)
class PlateauCluster:
    cluster_id: str
    members: tuple[str, ...]
    centroid: tuple[float, ...]
    size: int
    intra_variance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "members": list(self.members),
            "centroid": list(self.centroid),
            "size": self.size,
            "intra_variance": self.intra_variance,
        }


def _l1(
    a: Sequence[float], b: Sequence[float],
) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _centroid(
    samples: list[PlateauFeatures],
) -> tuple[float, ...]:
    if not samples:
        return ()
    dim = len(samples[0].feature_vector())
    sums = [0.0] * dim
    for s in samples:
        for i, v in enumerate(s.feature_vector()):
            sums[i] += v
    return tuple(s / len(samples) for s in sums)


def _intra_variance(
    samples: list[PlateauFeatures],
    centroid: tuple[float, ...],
) -> float:
    if not samples:
        return 0.0
    sq = 0.0
    for s in samples:
        v = s.feature_vector()
        sq += sum(
            (x - c) * (x - c) for x, c in zip(v, centroid)
        )
    return round(sq / len(samples), 6)


def cluster(
    features: tuple[PlateauFeatures, ...],
) -> tuple[PlateauCluster, ...]:
    if not features:
        return ()
    ordered = sorted(features, key=lambda s: s.trajectory_id)
    members: list[list[PlateauFeatures]] = []
    centroids: list[tuple[float, ...]] = []
    for s in ordered:
        vec = s.feature_vector()
        best_idx = -1
        best_dist = float("inf")
        for i, c in enumerate(centroids):
            d = _l1(vec, c)
            if d < best_dist:
                best_dist = d
                best_idx = i
        if (
            best_idx >= 0
            and best_dist <= _CLUSTER_TOLERANCE
        ):
            members[best_idx].append(s)
            centroids[best_idx] = _centroid(
                members[best_idx],
            )
        else:
            members.append([s])
            centroids.append(vec)
    # Round centroids; sort clusters by size desc.
    out: list[PlateauCluster] = []
    for i, m in enumerate(members):
        rounded = tuple(round(c, 6) for c in centroids[i])
        out.append(PlateauCluster(
            cluster_id=f"PC{i+1:02d}",
            members=tuple(s.trajectory_id for s in m),
            centroid=rounded, size=len(m),
            intra_variance=_intra_variance(m, centroids[i]),
        ))
    out.sort(key=lambda c: (-c.size, c.cluster_id))
    return tuple(
        PlateauCluster(
            cluster_id=f"PC{i+1:02d}",
            members=c.members, centroid=c.centroid,
            size=c.size, intra_variance=c.intra_variance,
        )
        for i, c in enumerate(out)
    )


__all__ = [
    "PlateauCluster", "cluster",
]
