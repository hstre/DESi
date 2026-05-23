"""v3.109 — re-evaluate the v3.108 small-vocab
under metadata ablation.

For each v3.105 hidden entanglement instance we:

* anonymize every member id (v3.109 transformer),
* re-compute every candidate dim against the
  ANONYMIZED id but ORIGINAL text,
* re-pick the best dim per instance,
* re-measure AUC and purity.

A candidate that survives metadata ablation must
NOT depend on the id. Those that collapse to a
constant under the transformer are recorded in
``collapsed_candidates``.
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
from ..t10_adaptive.adaptive import (
    ALL_CANDIDATES, adaptive_value,
)
from ..t10_generalization.census import (
    candidate_families,
)
from ..t10_transfer.inject import (
    all_transfer_outcomes,
)
from .metadata import anonymize_id


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
def _texts_by_id() -> dict[str, str]:
    return {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
    }


@lru_cache(maxsize=1)
def _vectors_by_id() -> dict[
    str, tuple[float, ...],
]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
    }


def _augmented_anon(
    member_ids: tuple[str, ...],
    candidate: str,
) -> dict[str, tuple[float, ...]]:
    """Build augmented vectors using ANONYMIZED
    ids for the candidate, but real vectors as
    the 45-d base."""
    vecs = _vectors_by_id()
    texts = _texts_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        anon = anonymize_id(mid)
        v = adaptive_value(
            candidate, anon, texts.get(mid, ""),
        )
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
class MetadataAblationOutcome:
    family_a: str
    family_b: str
    best_candidate: str
    best_auc: float
    best_purity: float
    rescued: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a": self.family_a,
            "family_b": self.family_b,
            "best_candidate":
                self.best_candidate,
            "best_auc": self.best_auc,
            "best_purity": self.best_purity,
            "rescued": self.rescued,
        }


@lru_cache(maxsize=1)
def all_metadata_ablation_outcomes() -> tuple[
    MetadataAblationOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[MetadataAblationOutcome] = []
    for tr in all_transfer_outcomes():
        a = fams_by_id.get(tr.family_a)
        b = fams_by_id.get(tr.family_b)
        if a is None or b is None:
            continue
        member_ids = tuple(
            sorted(set(a.member_ids + b.member_ids)),
        )
        best_cand = ""
        best_auc = 0.0
        best_pur = 0.0
        for cand in ALL_CANDIDATES:
            vecs = _augmented_anon(
                member_ids, cand,
            )
            auc = _pairwise_auc(vecs)
            if auc > best_auc or (
                auc == best_auc
                and cand < best_cand
            ):
                best_auc = auc
                best_cand = cand
                best_pur = _pairwise_purity(vecs)
        rescued = best_auc >= (
            _RESCUE_AUC_THRESHOLD
        )
        out.append(MetadataAblationOutcome(
            family_a=tr.family_a,
            family_b=tr.family_b,
            best_candidate=(
                best_cand if rescued else ""
            ),
            best_auc=best_auc,
            best_purity=best_pur,
            rescued=rescued,
        ))
    return tuple(out)


def collapsed_candidates() -> tuple[str, ...]:
    """Candidates whose anonymized-id evaluation
    yields a constant column across the
    entangled pool (zero pairwise distance
    contribution everywhere)."""
    members = set()
    for o in all_metadata_ablation_outcomes():
        for f in candidate_families():
            if f.family_id == o.family_a:
                members.update(f.member_ids)
            if f.family_id == o.family_b:
                members.update(f.member_ids)
    texts = _texts_by_id()
    collapsed: list[str] = []
    for cand in ALL_CANDIDATES:
        vals = {
            adaptive_value(
                cand,
                anonymize_id(mid),
                texts.get(mid, ""),
            )
            for mid in members
        }
        if len(vals) <= 1:
            collapsed.append(cand)
    return tuple(sorted(collapsed))


__all__ = [
    "MetadataAblationOutcome",
    "all_metadata_ablation_outcomes",
    "collapsed_candidates",
]
