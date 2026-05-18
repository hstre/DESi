"""v3.101 — candidate dimension scoring.

For each candidate dimension we augment the
v3.89 residual vector (45-d) with the candidate's
per-anchor value (one extra slot per state ⇒ +5
slots), then re-measure:

* ``candidate_auc``    - pairwise ROC AUC against
  same_family on the entangled pair.
* ``candidate_purity`` - single-link blind cluster
  purity using the augmented vector.
* ``candidate_margin`` - (min positive score) -
  (max negative score). Positive = fully
  separable.

The best candidate is the one with the highest
AUC; ties are broken by purity, then alphabetical.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    BlindCluster, largest_gap_threshold,
    pairwise_distances, single_link_cluster,
)
from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
    entangled_residual_vectors,
)
from ..field_leakage.distance import euclidean
from ..novel_families import all_family_members
from .candidate import (
    CANDIDATE_DIMS, candidate_values,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=None)
def augmented_vectors(
    candidate: str,
) -> dict[str, tuple[float, ...]]:
    """45-d residual vector with the candidate's
    value broadcast into 5 extra slots so the
    augmented vector has 50 dims."""
    base = entangled_residual_vectors()
    vals = candidate_values(candidate)
    out: dict[str, tuple[float, ...]] = {}
    for tid, vec in base.items():
        v = vals.get(tid, 0.0)
        out[tid] = vec + (v, v, v, v, v)
    return out


def _pairwise_auc(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _family_lookup()
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        s = -euclidean(vecs[a], vecs[b])
        if fam.get(a) == fam.get(b):
            pos.append(s)
        else:
            neg.append(s)
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return _round(
        (wins + 0.5 * ties)
        / (len(pos) * len(neg)),
    )


def _pairwise_margin(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _family_lookup()
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        s = -euclidean(vecs[a], vecs[b])
        if fam.get(a) == fam.get(b):
            pos.append(s)
        else:
            neg.append(s)
    if not pos or not neg:
        return 0.0
    return _round(min(pos) - max(neg))


def _cluster_purity(
    vecs: dict[str, tuple[float, ...]],
) -> tuple[float, tuple[BlindCluster, ...]]:
    dists = pairwise_distances(vecs)
    if not dists:
        return 0.0, ()
    thr = largest_gap_threshold(dists)
    clusters = single_link_cluster(vecs, dists, thr)
    fam = _family_lookup()
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0, clusters
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            counts[fam.get(m, "?")] = (
                counts.get(fam.get(m, "?"), 0)
                + 1
            )
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total), clusters


@dataclass(frozen=True)
class CandidateOutcome:
    candidate: str
    augmented_dim: int
    auc: float
    purity: float
    margin: float
    cluster_count: int
    cluster_sizes: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate,
            "augmented_dim": self.augmented_dim,
            "auc": self.auc,
            "purity": self.purity,
            "margin": self.margin,
            "cluster_count": self.cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
        }


@lru_cache(maxsize=1)
def all_candidate_outcomes() -> tuple[
    CandidateOutcome, ...,
]:
    out: list[CandidateOutcome] = []
    for c in CANDIDATE_DIMS:
        vecs = augmented_vectors(c)
        sample = next(iter(vecs.values()))
        auc = _pairwise_auc(vecs)
        margin = _pairwise_margin(vecs)
        purity, clusters = _cluster_purity(vecs)
        out.append(CandidateOutcome(
            candidate=c,
            augmented_dim=len(sample),
            auc=auc,
            purity=purity,
            margin=margin,
            cluster_count=len(clusters),
            cluster_sizes=tuple(
                len(cl.members) for cl in clusters
            ),
        ))
    return tuple(out)


def best_outcome() -> CandidateOutcome:
    outs = all_candidate_outcomes()
    return max(
        outs,
        key=lambda o: (
            o.auc, o.purity, o.margin, o.candidate,
        ),
    )


def candidates_above_auc_threshold(
    threshold: float = 0.70,
) -> tuple[str, ...]:
    return tuple(
        o.candidate
        for o in all_candidate_outcomes()
        if o.auc >= threshold
    )


def has_dominant_candidate(
    delta: float = 0.05,
) -> bool:
    """True iff the best candidate's AUC is
    strictly more than ``delta`` above every
    other candidate's AUC."""
    outs = list(all_candidate_outcomes())
    if len(outs) < 2:
        return False
    outs.sort(key=lambda o: -o.auc)
    return (outs[0].auc - outs[1].auc) > delta


__all__ = [
    "CandidateOutcome",
    "all_candidate_outcomes",
    "augmented_vectors",
    "best_outcome",
    "candidates_above_auc_threshold",
    "has_dominant_candidate",
]
