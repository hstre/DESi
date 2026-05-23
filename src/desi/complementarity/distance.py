"""v3.61 — plateau-pair distance primitives.

Computes Euclidean distance between every plateau-
anchor pair on the v3.50 9-d feature vector and
classifies each pair by the distance MEDIAN threshold
into ``high_d`` or ``low_d`` bins.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import statistics

from ..field_leakage.census import (
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


@dataclass(frozen=True)
class PairDistance:
    a: str
    b: str
    distance: float


@lru_cache(maxsize=1)
def plateau_pair_distances() -> tuple[
    PairDistance, ...,
]:
    plats = list(collect_plateau_anchors())
    vecs = [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in plats
    ]
    out: list[PairDistance] = []
    for (a, av), (b, bv) in combinations(vecs, 2):
        out.append(PairDistance(
            a=a, b=b, distance=euclidean(av, bv),
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def distance_threshold() -> float:
    distances = [
        p.distance for p in plateau_pair_distances()
    ]
    return statistics.median(distances)


def distance_bucket(distance: float) -> str:
    return "high_d" if distance > distance_threshold() else "low_d"


__all__ = [
    "PairDistance", "distance_bucket",
    "distance_threshold", "plateau_pair_distances",
]
