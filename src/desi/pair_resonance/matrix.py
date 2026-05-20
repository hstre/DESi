"""v3.50 — pair and triple resonance matrix.

For every unordered pair (and triple) of plateau
anchors, record |A|, |B|, |A∪B| and the strict
subadditivity gap ``|A| + |B| - |A∪B|``. Triples
add ``|A∪B∪C|`` and the inclusion-exclusion gap.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .coverage import AnchorCoverage


@dataclass(frozen=True)
class PairRecord:
    a: str
    b: str
    size_a: int
    size_b: int
    union_size: int
    intersection_size: int
    subadditivity_gap: int
    resonant: bool          # neither A subset B nor B subset A

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b,
            "size_a": self.size_a,
            "size_b": self.size_b,
            "union_size": self.union_size,
            "intersection_size":
                self.intersection_size,
            "subadditivity_gap":
                self.subadditivity_gap,
            "resonant": self.resonant,
        }


@dataclass(frozen=True)
class TripleRecord:
    a: str
    b: str
    c: str
    size_a: int
    size_b: int
    size_c: int
    union_size: int
    pair_max_union: int     # max |X∪Y| over the 3 pairs
    triple_extra: int       # |A∪B∪C| - pair_max_union

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b, "c": self.c,
            "size_a": self.size_a,
            "size_b": self.size_b,
            "size_c": self.size_c,
            "union_size": self.union_size,
            "pair_max_union": self.pair_max_union,
            "triple_extra": self.triple_extra,
        }


def _is_resonant(a: frozenset, b: frozenset) -> bool:
    """Neither anchor's coverage is a subset of the
    other AND the pair captures something neither
    captured alone."""
    if not a or not b:
        return False
    if a <= b or b <= a:
        return False
    return True


def build_pair_records(
    coverages: tuple[AnchorCoverage, ...],
) -> tuple[PairRecord, ...]:
    by_id = {c.anchor_id: c for c in coverages}
    ids = sorted(by_id.keys())
    out: list[PairRecord] = []
    for a, b in combinations(ids, 2):
        ca = by_id[a].coverage
        cb = by_id[b].coverage
        union = ca | cb
        inter = ca & cb
        gap = len(ca) + len(cb) - len(union)
        out.append(PairRecord(
            a=a, b=b,
            size_a=len(ca), size_b=len(cb),
            union_size=len(union),
            intersection_size=len(inter),
            subadditivity_gap=gap,
            resonant=_is_resonant(ca, cb),
        ))
    return tuple(out)


def build_triple_records(
    coverages: tuple[AnchorCoverage, ...],
    limit: int | None = None,
) -> tuple[TripleRecord, ...]:
    by_id = {c.anchor_id: c for c in coverages}
    ids = sorted(by_id.keys())
    out: list[TripleRecord] = []
    for i, (a, b, c) in enumerate(
        combinations(ids, 3),
    ):
        ca = by_id[a].coverage
        cb = by_id[b].coverage
        cc = by_id[c].coverage
        union3 = ca | cb | cc
        u_ab = len(ca | cb)
        u_ac = len(ca | cc)
        u_bc = len(cb | cc)
        pair_max = max(u_ab, u_ac, u_bc)
        out.append(TripleRecord(
            a=a, b=b, c=c,
            size_a=len(ca), size_b=len(cb),
            size_c=len(cc),
            union_size=len(union3),
            pair_max_union=pair_max,
            triple_extra=len(union3) - pair_max,
        ))
        if limit is not None and len(out) >= limit:
            break
    return tuple(out)


def pair_matrix(
    coverages: tuple[AnchorCoverage, ...],
) -> dict[str, dict[str, int]]:
    by_id = {c.anchor_id: c for c in coverages}
    ids = sorted(by_id.keys())
    out: dict[str, dict[str, int]] = {}
    for a in ids:
        row: dict[str, int] = {}
        for b in ids:
            row[b] = len(
                by_id[a].coverage | by_id[b].coverage,
            )
        out[a] = row
    return out


__all__ = [
    "PairRecord", "TripleRecord",
    "build_pair_records", "build_triple_records",
    "pair_matrix",
]
