"""v3.62 — anchor coverage primitives.

Builds per-anchor leakage coverage at the v3.50 probe
radius (3.5) and per-pair set arithmetic (union,
intersection, symmetric difference) for blind-spot
analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5


@dataclass(frozen=True)
class AnchorCoverage:
    anchor_id: str
    coverage: frozenset[int]

    @property
    def size(self) -> int:
        return len(self.coverage)


@dataclass(frozen=True)
class PairCoverage:
    a: str
    b: str
    size_a: int
    size_b: int
    union_size: int
    intersection_size: int
    symmetric_diff_size: int
    coverage_gain: int      # |union| - max(|a|, |b|)
    redundancy: float       # |intersect| / min(|a|, |b|)
    new_region_fraction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b,
            "size_a": self.size_a,
            "size_b": self.size_b,
            "union_size": self.union_size,
            "intersection_size":
                self.intersection_size,
            "symmetric_diff_size":
                self.symmetric_diff_size,
            "coverage_gain": self.coverage_gain,
            "redundancy": self.redundancy,
            "new_region_fraction":
                self.new_region_fraction,
        }


def _coverage_set(
    anchor_vec: tuple[float, ...],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> frozenset[int]:
    return frozenset(
        i for i, lv in enumerate(leakage_vecs)
        if euclidean(anchor_vec, lv) <= radius
    )


@lru_cache(maxsize=1)
def all_leakage_vectors(
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        trajectory_vector(t.states)
        for t in collect_leakage_trajectories()
    )


@lru_cache(maxsize=1)
def all_anchor_coverages(
) -> tuple[AnchorCoverage, ...]:
    leak_vecs = list(all_leakage_vectors())
    out: list[AnchorCoverage] = []
    for t in collect_plateau_anchors():
        av = trajectory_vector(t.states)
        out.append(AnchorCoverage(
            anchor_id=t.trajectory_id,
            coverage=_coverage_set(
                av, leak_vecs, PROBE_RADIUS,
            ),
        ))
    return tuple(out)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def pair_coverage(
    a: AnchorCoverage, b: AnchorCoverage,
) -> PairCoverage:
    ca, cb = a.coverage, b.coverage
    union = ca | cb
    inter = ca & cb
    sd = ca ^ cb
    larger = max(len(ca), len(cb))
    smaller = min(len(ca), len(cb))
    gain = len(union) - larger
    redundancy = (
        _round(len(inter) / smaller)
        if smaller > 0 else 0.0
    )
    new_frac = (
        _round(len(sd) / len(union))
        if union else 0.0
    )
    return PairCoverage(
        a=a.anchor_id, b=b.anchor_id,
        size_a=len(ca), size_b=len(cb),
        union_size=len(union),
        intersection_size=len(inter),
        symmetric_diff_size=len(sd),
        coverage_gain=gain,
        redundancy=redundancy,
        new_region_fraction=new_frac,
    )


__all__ = [
    "AnchorCoverage", "PROBE_RADIUS", "PairCoverage",
    "all_anchor_coverages", "all_leakage_vectors",
    "pair_coverage",
]
