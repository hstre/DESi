"""v3.105 — corpus-wide hidden entanglement census.

A *hidden entanglement* is a pair of distinct claim
families that

* have low token-Jaccard overlap (high semantic
  distance), AND
* collapse onto the same trajectory-tail centroid
  (low state-space distance).

We enumerate every family of size >= 3 in the
corpus (excluding G_v316susp + E_v317h, the known
pair) and group them by their family centroid; any
centroid shared by two or more families with low
mutual text overlap is a hidden entanglement.

Closed definitions:

* family key = ``"<corpus>:<letter_prefix>"``,
  derived deterministically from the trajectory id.
* centroid     = element-wise mean of the 45-d
  trajectory tail vectors, rounded to 6 dp so
  collapsed points hash identically.
* token_overlap = unigram Jaccard between the
  union of all family-member texts.
"""
from __future__ import annotations

import itertools
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


_MIN_FAMILY_SIZE: int = 3
_MIN_STATE_COUNT: int = 5
_SEMANTIC_OVERLAP_CEILING: float = 0.10
_CENTROID_DISTANCE_TOLERANCE: float = 0.001


_TOKEN_RE = re.compile(r"[a-zA-Z]+")
_MIN_TOKEN_LEN: int = 3


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_key(trajectory_id: str) -> str | None:
    if ":" not in trajectory_id:
        return None
    corpus, tail = trajectory_id.split(":", 1)
    m = re.match(r"([A-Za-z]+)", tail)
    if not m:
        return None
    return f"{corpus}:{m.group(1)}"


def _tokens(text: str) -> set[str]:
    return {
        t.lower()
        for t in _TOKEN_RE.findall(text.lower())
        if len(t) >= _MIN_TOKEN_LEN
    }


@dataclass(frozen=True)
class CensusFamily:
    family_id: str
    member_ids: tuple[str, ...]
    centroid: tuple[float, ...]
    token_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "family_id": self.family_id,
            "member_ids": list(self.member_ids),
            "centroid": list(self.centroid),
            "token_count": self.token_count,
        }


_EXCLUDED_PAIR: tuple[str, str] = (
    "v316-susp:G",
    "v317-h:E",
)


@lru_cache(maxsize=1)
def candidate_families() -> tuple[CensusFamily, ...]:
    by: dict[str, list] = defaultdict(list)
    for t in extract_all_trajectories():
        if not t.text:
            continue
        if len(t.states) < _MIN_STATE_COUNT:
            continue
        key = _family_key(t.trajectory_id)
        if key is None:
            continue
        if key in _EXCLUDED_PAIR:
            continue
        by[key].append(t)
    out: list[CensusFamily] = []
    for key, members in sorted(by.items()):
        if len(members) < _MIN_FAMILY_SIZE:
            continue
        vecs = [
            trajectory_vector(t.states)
            for t in members
        ]
        d = len(vecs[0]) if vecs else 0
        cent = tuple(
            _round(
                sum(v[i] for v in vecs) / len(vecs),
            )
            for i in range(d)
        )
        token_count = sum(
            len(_tokens(t.text)) for t in members
        )
        out.append(CensusFamily(
            family_id=key,
            member_ids=tuple(
                sorted(t.trajectory_id for t in members),
            ),
            centroid=cent,
            token_count=token_count,
        ))
    return tuple(out)


def _token_jaccard(
    a: CensusFamily, b: CensusFamily,
) -> float:
    a_toks: set[str] = set()
    b_toks: set[str] = set()
    by_id = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    for tid in a.member_ids:
        a_toks |= _tokens(by_id[tid].text)
    for tid in b.member_ids:
        b_toks |= _tokens(by_id[tid].text)
    union = a_toks | b_toks
    if not union:
        return 0.0
    return _round(len(a_toks & b_toks) / len(union))


@dataclass(frozen=True)
class EntanglementInstance:
    family_a: str
    family_b: str
    text_overlap: float
    centroid_distance: float
    centroid: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a": self.family_a,
            "family_b": self.family_b,
            "text_overlap": self.text_overlap,
            "centroid_distance":
                self.centroid_distance,
            "centroid": list(self.centroid),
        }


@lru_cache(maxsize=1)
def all_entanglement_instances() -> tuple[
    EntanglementInstance, ...,
]:
    fams = candidate_families()
    out: list[EntanglementInstance] = []
    for a, b in itertools.combinations(fams, 2):
        overlap = _token_jaccard(a, b)
        if overlap >= _SEMANTIC_OVERLAP_CEILING:
            continue
        cdist = _round(
            euclidean(a.centroid, b.centroid),
        )
        if cdist > _CENTROID_DISTANCE_TOLERANCE:
            continue
        out.append(EntanglementInstance(
            family_a=a.family_id,
            family_b=b.family_id,
            text_overlap=overlap,
            centroid_distance=cdist,
            centroid=a.centroid,
        ))
    return tuple(out)


@dataclass(frozen=True)
class EntanglementType:
    type_id: int
    centroid: tuple[float, ...]
    families: tuple[str, ...]
    pair_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "type_id": self.type_id,
            "centroid": list(self.centroid),
            "families": list(self.families),
            "pair_count": self.pair_count,
        }


@lru_cache(maxsize=1)
def all_entanglement_types() -> tuple[
    EntanglementType, ...,
]:
    """Group entangled families by their shared
    centroid. Each group is one entanglement
    type."""
    by_centroid: dict[
        tuple[float, ...], set[str],
    ] = defaultdict(set)
    for inst in all_entanglement_instances():
        by_centroid[inst.centroid].add(inst.family_a)
        by_centroid[inst.centroid].add(inst.family_b)
    out: list[EntanglementType] = []
    for i, (cent, fams) in enumerate(
        sorted(
            by_centroid.items(),
            key=lambda kv: (-len(kv[1]), kv[0]),
        ),
    ):
        n = len(fams)
        out.append(EntanglementType(
            type_id=i,
            centroid=cent,
            families=tuple(sorted(fams)),
            pair_count=n * (n - 1) // 2,
        ))
    return tuple(out)


__all__ = [
    "CensusFamily",
    "EntanglementInstance",
    "EntanglementType",
    "all_entanglement_instances",
    "all_entanglement_types",
    "candidate_families",
]
