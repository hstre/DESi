"""v3.113 — per-candidate AUC + signal census.

For each structural candidate we measure:

* its per-anchor variance across the entangled
  pool,
* its pairwise AUC vs same_family on every
  v3.105 instance,
* its purity when used as a +1 dim.

A candidate is a "signal candidate" if its mean
pairwise AUC exceeds the chance baseline by at
least 0.05.
"""
from __future__ import annotations

import itertools
import statistics
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
from .topology import (
    STRUCTURAL_CANDIDATES,
    structural_value,
)


_SIGNAL_DELTA: float = 0.05


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
    candidate: str,
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        v = structural_value(candidate, mid)
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


def _pairwise_margin(
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
        return 0.0
    return _round(min(pos) - max(neg))


@dataclass(frozen=True)
class StructuralOutcome:
    candidate: str
    variance_on_entangled_pool: float
    mean_auc: float
    mean_purity: float
    mean_margin: float

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate,
            "variance_on_entangled_pool":
                self.variance_on_entangled_pool,
            "mean_auc": self.mean_auc,
            "mean_purity": self.mean_purity,
            "mean_margin": self.mean_margin,
        }


def _entangled_member_ids() -> tuple[str, ...]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: set[str] = set()
    for tr in all_transfer_outcomes():
        a = fams_by_id.get(tr.family_a)
        b = fams_by_id.get(tr.family_b)
        if a is None or b is None:
            continue
        out.update(a.member_ids)
        out.update(b.member_ids)
    return tuple(sorted(out))


@lru_cache(maxsize=1)
def all_structural_outcomes() -> tuple[
    StructuralOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    member_pool = _entangled_member_ids()
    out: list[StructuralOutcome] = []
    for cand in STRUCTURAL_CANDIDATES:
        # Variance over entangled pool.
        vals = [
            structural_value(cand, mid)
            for mid in member_pool
        ]
        var = (
            _round(statistics.pvariance(vals))
            if len(vals) >= 2 else 0.0
        )
        # Per-instance AUC / purity / margin.
        aucs: list[float] = []
        purs: list[float] = []
        mars: list[float] = []
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
            vecs = _augmented(ms, cand)
            aucs.append(_pairwise_auc(vecs))
            purs.append(_pairwise_purity(vecs))
            mars.append(_pairwise_margin(vecs))
        out.append(StructuralOutcome(
            candidate=cand,
            variance_on_entangled_pool=var,
            mean_auc=(
                _round(sum(aucs) / len(aucs))
                if aucs else 0.0
            ),
            mean_purity=(
                _round(sum(purs) / len(purs))
                if purs else 0.0
            ),
            mean_margin=(
                _round(sum(mars) / len(mars))
                if mars else 0.0
            ),
        ))
    return tuple(out)


def signal_candidates() -> tuple[str, ...]:
    return tuple(
        o.candidate
        for o in all_structural_outcomes()
        if o.mean_auc >= 0.5 + _SIGNAL_DELTA
    )


def top_candidate() -> StructuralOutcome:
    outs = all_structural_outcomes()
    return max(
        outs,
        key=lambda o: (
            o.mean_auc, o.mean_purity,
            o.mean_margin, o.candidate,
        ),
    )


__all__ = [
    "StructuralOutcome",
    "all_structural_outcomes",
    "signal_candidates",
    "top_candidate",
]
