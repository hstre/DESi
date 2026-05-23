"""v3.92 — pairwise family forecast on frame-
normalized novel anchors.

Same template as v3.88 (score = -euclidean
distance, label = same_family), but the input
vectors are the v3.89 residual projection.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..field_leakage.distance import euclidean
from ..frame_normalization.contribution import (
    novel_vectors_residual,
)
from ..novel_families import all_family_members


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class FrameNormalizedPairForecast:
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
def all_normalized_pair_forecasts() -> tuple[
    FrameNormalizedPairForecast, ...,
]:
    vecs = novel_vectors_residual()
    fam = _family_of()
    out: list[FrameNormalizedPairForecast] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        d = _round(euclidean(vecs[a], vecs[b]))
        out.append(FrameNormalizedPairForecast(
            anchor_a=a, anchor_b=b,
            family_a=fam.get(a, "?"),
            family_b=fam.get(b, "?"),
            distance=d,
            score=_round(-d),
            same_family=fam.get(a) == fam.get(b),
        ))
    return tuple(out)


__all__ = [
    "FrameNormalizedPairForecast",
    "all_normalized_pair_forecasts",
]
