"""v3.100 — representation comparison.

Two representations of the v3.93 entangled
(G_v316susp + E_v317h) pair:

* **A (separated)** - 45-d state vector + 1
  one-hot ``family_id`` channel. Total dim = 46;
  every anchor has a guaranteed-distinct
  ``family_id`` coordinate.
* **B (degenerate)** - 45-d state vector only.
  G and E collapse onto the same point set.

Closed structural metrics:

* ``dim_a`` = 46
* ``dim_b`` = 45
* ``distinct_point_count_a`` = number of unique
  46-d vectors across the 19 anchors.
* ``distinct_point_count_b`` = number of unique
  45-d vectors across the 19 anchors.
* ``compression_gain`` = 1 - (point_count_b /
  point_count_a) - how much smaller the
  degenerate representation is in distinct
  outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    trajectory_vector,
)
from ..novel_families import all_family_members


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=1)
def degenerate_vectors() -> dict[
    str, tuple[float, ...],
]:
    """Representation B - the production
    StateVector tail; this is what DESi's
    pipeline actually sees."""
    members = set(entangled_members())
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
        if t.trajectory_id in members
    }


@lru_cache(maxsize=1)
def separated_vectors() -> dict[
    str, tuple[float, ...],
]:
    """Representation A - degenerate vector plus
    a one-hot family_id channel (1.0 if first
    entangled family, 0.0 if second)."""
    fam = _family_lookup()
    a_id = ENTANGLED_FAMILY_IDS[0]
    out: dict[str, tuple[float, ...]] = {}
    for tid, vec in degenerate_vectors().items():
        family_id_one_hot = (
            1.0 if fam.get(tid) == a_id else 0.0
        )
        out[tid] = vec + (family_id_one_hot,)
    return out


def dim_a() -> int:
    """Dimensionality of representation A."""
    sample = next(iter(separated_vectors().values()))
    return len(sample)


def dim_b() -> int:
    sample = next(iter(degenerate_vectors().values()))
    return len(sample)


def distinct_point_count_a() -> int:
    return len(set(separated_vectors().values()))


def distinct_point_count_b() -> int:
    return len(set(degenerate_vectors().values()))


def compression_gain() -> float:
    """Fraction of distinct points that the
    degenerate representation collapses. 0 means
    no collapse; 1 means everything collapses to
    a single point."""
    a = distinct_point_count_a()
    if a == 0:
        return 0.0
    return _round(1.0 - distinct_point_count_b() / a)


def collapsed_anchor_count() -> int:
    """Number of anchors that share a point with
    at least one OTHER anchor in representation
    B - the population that representation A
    keeps distinct."""
    vecs = degenerate_vectors()
    by_vec: dict[tuple[float, ...], list[str]] = {}
    for tid, v in vecs.items():
        by_vec.setdefault(v, []).append(tid)
    return sum(
        len(ids) for ids in by_vec.values()
        if len(ids) > 1
    )


__all__ = [
    "collapsed_anchor_count",
    "compression_gain",
    "degenerate_vectors",
    "dim_a", "dim_b",
    "distinct_point_count_a",
    "distinct_point_count_b",
    "separated_vectors",
]
