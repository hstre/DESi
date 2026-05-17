"""v3.85 — novel family isolation primitives.

Per family we compute:

* anchor_count - members surviving the prior-sprint
  overlap filter;
* overlap_with_prior - members that overlap the
  forbidden anchor pool (must equal 0);
* family_variance - mean pairwise Euclidean distance
  on the 45-d tail-vector inside the family;
* family_max_intra - the largest pairwise distance;
* family_centroid_norm - ||centroid|| for sanity.

Cross-family separability is the minimum and mean
pairwise distance between the two member sets.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from .select import (
    FORBIDDEN_ANCHORS, NOVEL_FAMILY_SPECS,
    NovelFamilySpec, all_family_members,
    family_members,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _trajectory_vectors(
) -> dict[str, tuple[float, ...]]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
    }


def _centroid(
    vecs: list[tuple[float, ...]],
) -> tuple[float, ...]:
    if not vecs:
        return ()
    d = len(vecs[0])
    n = len(vecs)
    return tuple(
        sum(v[i] for v in vecs) / n
        for i in range(d)
    )


def _norm(v: tuple[float, ...]) -> float:
    return sum(x * x for x in v) ** 0.5


@dataclass(frozen=True)
class NovelFamily:
    family_id: str
    corpus: str
    letter: str
    rationale: str
    members: tuple[str, ...]
    anchor_count: int
    overlap_with_prior: int
    family_variance: float
    family_max_intra: float
    family_centroid_norm: float

    def to_dict(self) -> dict[str, object]:
        return {
            "family_id": self.family_id,
            "corpus": self.corpus,
            "letter": self.letter,
            "rationale": self.rationale,
            "members": list(self.members),
            "anchor_count": self.anchor_count,
            "overlap_with_prior":
                self.overlap_with_prior,
            "family_variance":
                self.family_variance,
            "family_max_intra":
                self.family_max_intra,
            "family_centroid_norm":
                self.family_centroid_norm,
        }


def isolate_family(
    spec: NovelFamilySpec,
    vecs: dict[str, tuple[float, ...]],
) -> NovelFamily:
    members = family_members(spec)
    # overlap_with_prior counts SELECTED members that
    # still fall inside the forbidden pool. By
    # construction select.family_members removes
    # them, so this must be 0 - any non-zero value
    # surfaces a drift in the prior-sprint sources.
    overlap = sum(
        1 for tid in members
        if tid in FORBIDDEN_ANCHORS
    )
    fvecs = [vecs[m] for m in members]
    pairs = list(itertools.combinations(
        range(len(fvecs)), 2,
    ))
    intra = [
        euclidean(fvecs[i], fvecs[j])
        for i, j in pairs
    ]
    variance = (
        _round(sum(intra) / len(intra))
        if intra else 0.0
    )
    max_intra = (
        _round(max(intra)) if intra else 0.0
    )
    centroid_norm = (
        _round(_norm(_centroid(fvecs)))
        if fvecs else 0.0
    )
    return NovelFamily(
        family_id=spec.family_id,
        corpus=spec.corpus,
        letter=spec.letter,
        rationale=spec.rationale,
        members=members,
        anchor_count=len(members),
        overlap_with_prior=overlap,
        family_variance=variance,
        family_max_intra=max_intra,
        family_centroid_norm=centroid_norm,
    )


def all_novel_families() -> tuple[NovelFamily, ...]:
    vecs = _trajectory_vectors()
    return tuple(
        isolate_family(s, vecs)
        for s in NOVEL_FAMILY_SPECS
    )


@dataclass(frozen=True)
class FamilySeparation:
    family_a_id: str
    family_b_id: str
    min_distance: float
    mean_distance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a_id": self.family_a_id,
            "family_b_id": self.family_b_id,
            "min_distance": self.min_distance,
            "mean_distance": self.mean_distance,
        }


def pairwise_family_separations(
) -> tuple[FamilySeparation, ...]:
    vecs = _trajectory_vectors()
    members = all_family_members()
    fids = list(members)
    out: list[FamilySeparation] = []
    for i in range(len(fids)):
        for j in range(i + 1, len(fids)):
            a, b = members[fids[i]], members[fids[j]]
            ds = [
                euclidean(vecs[x], vecs[y])
                for x in a for y in b
            ]
            if not ds:
                continue
            out.append(FamilySeparation(
                family_a_id=fids[i],
                family_b_id=fids[j],
                min_distance=_round(min(ds)),
                mean_distance=_round(
                    sum(ds) / len(ds),
                ),
            ))
    return tuple(out)


__all__ = [
    "FamilySeparation",
    "NovelFamily",
    "all_novel_families",
    "isolate_family",
    "pairwise_family_separations",
]
