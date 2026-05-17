"""v3.38 — pairwise distance + per-dimension comparison.

Pure-Python Euclidean over a fixed-shape feature vector.
The feature vector for a trajectory is the concatenation
of its state vectors (T x 9 floats). All v3.35 movers
(20 plateau + 14 unexpected rescues) have T = 5, so the
vector length is 45.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


def trajectory_vector(
    states: tuple[StateVector, ...],
) -> tuple[float, ...]:
    out: list[float] = []
    for s in states:
        out.extend(s.to_tuple())
    return tuple(out)


def per_state_value(
    states: tuple[StateVector, ...], dim: str, index: int,
) -> float:
    """One scalar from one state of one trajectory.
    ``index`` may be negative (Pythonic indexing)."""
    return getattr(states[index], dim)


def euclidean(
    a: tuple[float, ...], b: tuple[float, ...],
) -> float:
    if len(a) != len(b):
        raise ValueError("vector length mismatch")
    return sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


@dataclass(frozen=True)
class PairwiseDistance:
    a_id: str
    b_id: str
    distance: float
    same_class: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "a_id": self.a_id, "b_id": self.b_id,
            "distance": self.distance,
            "same_class": self.same_class,
        }


def pairwise_distances(
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
) -> tuple[PairwiseDistance, ...]:
    """``items`` = sequence of (id, class_label, vector).
    Emits all unordered pairs (no i==j, no double-count)."""
    out: list[PairwiseDistance] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ai, ac, av = items[i]
            bi, bc, bv = items[j]
            out.append(PairwiseDistance(
                a_id=ai, b_id=bi,
                distance=euclidean(av, bv),
                same_class=(ac == bc),
            ))
    return tuple(out)


def overlap_rate(
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
) -> float:
    """Fraction of cross-class pairs whose feature vectors
    are bit-identical (distance == 0)."""
    cross = [
        d for d in pairwise_distances(items)
        if not d.same_class
    ]
    if not cross:
        return 0.0
    identical = sum(1 for d in cross if d.distance == 0.0)
    return round(identical / len(cross), 6)


__all__ = [
    "DIMENSION_NAMES", "PairwiseDistance", "euclidean",
    "overlap_rate", "pairwise_distances",
    "per_state_value", "trajectory_vector",
]
