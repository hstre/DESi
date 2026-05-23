"""v3.114 — recovery metrics for the single
structural candidate.

For every v3.105 entanglement instance we:

* augment the residual vector with one +1 slot
  equal to ``structural_value(top, member_id)``,
* re-measure AUC, purity, and rescue status.

Because v3.113 showed every structural candidate
collapses to a constant on the entangled pool,
the augmented vector adds a constant slot ⇒
pairwise distances unchanged ⇒ AUC unchanged ⇒
zero rescue.
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
from ..t10_generalization.census import (
    candidate_families,
)
from ..t10_transfer.inject import (
    all_transfer_outcomes,
)
from .inject import (
    selected_structural_candidate,
    structural_value,
)


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


def _augmented(
    member_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    cand = selected_structural_candidate()
    vecs = _vectors_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        v = structural_value(cand, mid)
        out[mid] = vecs[mid] + (v,)
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
class SingleStructuralOutcome:
    family_a: str
    family_b: str
    auc: float
    purity: float
    rescued: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a": self.family_a,
            "family_b": self.family_b,
            "auc": self.auc,
            "purity": self.purity,
            "rescued": self.rescued,
        }


@lru_cache(maxsize=1)
def all_outcomes() -> tuple[
    SingleStructuralOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[SingleStructuralOutcome] = []
    for tr in all_transfer_outcomes():
        a = fams_by_id.get(tr.family_a)
        b = fams_by_id.get(tr.family_b)
        if a is None or b is None:
            continue
        ms = tuple(
            sorted(
                set(a.member_ids + b.member_ids),
            ),
        )
        vecs = _augmented(ms)
        auc = _pairwise_auc(vecs)
        pur = _pairwise_purity(vecs)
        out.append(SingleStructuralOutcome(
            family_a=tr.family_a,
            family_b=tr.family_b,
            auc=auc,
            purity=pur,
            rescued=auc >= _RESCUE_AUC_THRESHOLD,
        ))
    return tuple(out)


def structural_recovery() -> float:
    outs = all_outcomes()
    if not outs:
        return 0.0
    n = sum(1 for o in outs if o.rescued)
    return _round(n / len(outs))


def structural_auc() -> float:
    outs = all_outcomes()
    if not outs:
        return 0.0
    return _round(
        sum(o.auc for o in outs) / len(outs),
    )


def structural_purity() -> float:
    outs = all_outcomes()
    if not outs:
        return 0.0
    return _round(
        sum(o.purity for o in outs) / len(outs),
    )


__all__ = [
    "SingleStructuralOutcome",
    "all_outcomes",
    "structural_auc",
    "structural_purity",
    "structural_recovery",
]
