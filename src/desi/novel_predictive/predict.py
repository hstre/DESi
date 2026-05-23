"""v3.88 — pairwise family forecast on novel
anchors.

For every pair ``(A, B)`` of v3.85 novel anchors we
form a pre-coverage forecast:

    score(A, B) = -euclidean(tail(A), tail(B))

Label: ``1`` iff A and B share a v3.85 family id;
``0`` otherwise. Coverage is never consulted - the
score sees only the 45-d trajectory tail vector.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..novel_families import all_family_members
from ..novel_family_cluster.distance import (
    novel_pairwise_distances,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class NovelPairForecast:
    anchor_a: str
    anchor_b: str
    family_a: str
    family_b: str
    distance: float
    score: float
    same_family: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "anchor_a": self.anchor_a,
            "anchor_b": self.anchor_b,
            "family_a": self.family_a,
            "family_b": self.family_b,
            "distance": self.distance,
            "score": self.score,
            "same_family": self.same_family,
        }


@lru_cache(maxsize=1)
def _family_of() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=1)
def all_novel_pair_forecasts() -> tuple[
    NovelPairForecast, ...,
]:
    fam = _family_of()
    out: list[NovelPairForecast] = []
    for a, b, d in novel_pairwise_distances():
        out.append(NovelPairForecast(
            anchor_a=a, anchor_b=b,
            family_a=fam.get(a, "?"),
            family_b=fam.get(b, "?"),
            distance=d,
            score=_round(-d),
            same_family=fam.get(a) == fam.get(b),
        ))
    return tuple(out)


__all__ = [
    "NovelPairForecast",
    "all_novel_pair_forecasts",
]
