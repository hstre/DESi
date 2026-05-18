"""v3.115 — exhaustive structural alphabet
search.

For sizes k = 1..MAX, enumerate every k-subset
of ``STRUCTURAL_CANDIDATES``, augment the
entangled vectors with k extra slots (one per
candidate), and re-measure aggregate AUC, purity,
and rescue rate.

If v3.113 is correct that every structural
candidate has zero variance on the entangled
pool, no subset of any size will rescue - all
augmented slots are constants, all augmented
vectors collapse to the same point.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    largest_gap_threshold,
    pairwise_distances,
    single_link_cluster,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..t10_deep.topology import (
    STRUCTURAL_CANDIDATES, structural_value,
)
from ..t10_generalization.census import (
    candidate_families,
)
from ..t10_transfer.inject import (
    all_transfer_outcomes,
)


MAX_VOCAB_SIZE: int = 3
_RESCUE_AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _families_by_id() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in candidate_families():
        for mid in f.member_ids:
            out[mid] = f.family_id
    return out


@lru_cache(maxsize=1)
def _vectors_by_id() -> dict[
    str, tuple[float, ...],
]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
    }


def _augmented_with_subset(
    member_ids: tuple[str, ...],
    subset: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        extras = tuple(
            structural_value(c, mid)
            for c in subset
        )
        out[mid] = vecs[mid] + extras
    return out


def _pairwise_auc(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _families_by_id()
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


def _pairwise_purity(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _families_by_id()
    dists = pairwise_distances(vecs)
    if not dists:
        return 0.0
    thr = largest_gap_threshold(dists)
    clusters = single_link_cluster(vecs, dists, thr)
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
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
    return _round(correct / total)


@dataclass(frozen=True)
class SubsetOutcome:
    subset: tuple[str, ...]
    mean_auc: float
    mean_purity: float
    rescue_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "subset": list(self.subset),
            "mean_auc": self.mean_auc,
            "mean_purity": self.mean_purity,
            "rescue_rate": self.rescue_rate,
        }


@lru_cache(maxsize=1)
def all_subset_outcomes() -> tuple[
    SubsetOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[SubsetOutcome] = []
    for k in range(1, MAX_VOCAB_SIZE + 1):
        for combo in itertools.combinations(
            STRUCTURAL_CANDIDATES, k,
        ):
            aucs: list[float] = []
            purs: list[float] = []
            rescued = 0
            for tr in all_transfer_outcomes():
                a = fams_by_id.get(tr.family_a)
                b = fams_by_id.get(tr.family_b)
                if a is None or b is None:
                    continue
                ms = tuple(
                    sorted(
                        set(
                            a.member_ids
                            + b.member_ids,
                        ),
                    ),
                )
                vecs = _augmented_with_subset(
                    ms, combo,
                )
                auc = _pairwise_auc(vecs)
                pur = _pairwise_purity(vecs)
                aucs.append(auc)
                purs.append(pur)
                if auc >= _RESCUE_AUC_THRESHOLD:
                    rescued += 1
            out.append(SubsetOutcome(
                subset=tuple(sorted(combo)),
                mean_auc=(
                    _round(sum(aucs) / len(aucs))
                    if aucs else 0.0
                ),
                mean_purity=(
                    _round(sum(purs) / len(purs))
                    if purs else 0.0
                ),
                rescue_rate=(
                    _round(rescued / len(aucs))
                    if aucs else 0.0
                ),
            ))
    return tuple(out)


def best_subset() -> SubsetOutcome:
    outs = all_subset_outcomes()
    return max(
        outs,
        key=lambda o: (
            o.rescue_rate, o.mean_auc,
            o.mean_purity, -len(o.subset),
            o.subset,
        ),
    )


__all__ = [
    "MAX_VOCAB_SIZE",
    "SubsetOutcome",
    "all_subset_outcomes",
    "best_subset",
]
