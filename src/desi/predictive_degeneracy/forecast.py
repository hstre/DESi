"""v3.84 — pairwise doppelganger forecast.

For each pair of plateau anchors (A, B) compute a
pre-coverage score from the tail-vector distance:

    score(A, B) = -euclidean(tail(A), tail(B))

Label: 1 if A and B share a v3.79 redundancy class,
0 otherwise. The forecast never sees coverage
counts or class IDs - only the 45-d trajectory tail
vectors.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    pairwise_distances, plateau_anchor_vectors,
)
from ..redundancy_masking.equivalence import (
    redundancy_classes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class PairForecast:
    anchor_a: str
    anchor_b: str
    distance: float
    score: float
    same_class: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "anchor_a": self.anchor_a,
            "anchor_b": self.anchor_b,
            "distance": self.distance,
            "score": self.score,
            "same_class": self.same_class,
        }


@lru_cache(maxsize=1)
def _class_of() -> dict[str, int]:
    out: dict[str, int] = {}
    for c in redundancy_classes():
        for m in c.members:
            out[m] = c.class_id
    return out


@lru_cache(maxsize=1)
def all_pair_forecasts() -> tuple[
    PairForecast, ...,
]:
    vecs = plateau_anchor_vectors()
    dists = pairwise_distances(vecs)
    cls = _class_of()
    out: list[PairForecast] = []
    for a, b, d in dists:
        out.append(PairForecast(
            anchor_a=a, anchor_b=b,
            distance=d, score=_round(-d),
            same_class=(
                cls.get(a, -1) == cls.get(b, -2)
            ),
        ))
    return tuple(out)


def roc_auc(
    pairs: tuple[PairForecast, ...],
) -> float:
    pos = [p.score for p in pairs if p.same_class]
    neg = [
        p.score for p in pairs if not p.same_class
    ]
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    total = len(pos) * len(neg)
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return _round((wins + 0.5 * ties) / total)


def predictive_auc() -> float:
    return roc_auc(all_pair_forecasts())


def forecast_margin() -> float:
    """Largest positive-class score minus smallest
    negative-class score. Positive => fully
    separable; negative => overlapping
    distributions."""
    pairs = all_pair_forecasts()
    pos = [p.score for p in pairs if p.same_class]
    neg = [
        p.score for p in pairs if not p.same_class
    ]
    if not pos or not neg:
        return 0.0
    return _round(min(pos) - max(neg))


def optimal_threshold() -> float:
    """Midpoint of the gap between the worst
    positive score and the best negative score."""
    pairs = all_pair_forecasts()
    pos = sorted(
        p.score for p in pairs if p.same_class
    )
    neg = sorted(
        p.score for p in pairs if not p.same_class
    )
    if not pos or not neg:
        return 0.0
    return _round((min(pos) + max(neg)) / 2.0)


def false_positive_rate(threshold: float) -> float:
    pairs = all_pair_forecasts()
    neg = [p for p in pairs if not p.same_class]
    if not neg:
        return 0.0
    fp = sum(1 for p in neg if p.score >= threshold)
    return _round(fp / len(neg))


__all__ = [
    "PairForecast",
    "all_pair_forecasts",
    "false_positive_rate", "forecast_margin",
    "optimal_threshold", "predictive_auc",
    "roc_auc",
]
