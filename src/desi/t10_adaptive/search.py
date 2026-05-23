"""v3.107 — per-instance adaptive search.

For each previously-unrescued entanglement, find
the minimal candidate dimension (from
``ALL_CANDIDATES``) that achieves AUC >= 0.70 on
that instance. If multiple candidates tie, pick
the alphabetically smallest. If none rescue,
record ``best_candidate = ""`` and the highest
AUC found.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

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
from .adaptive import (
    ALL_CANDIDATES, candidate_values_for_ids,
)


_RESCUE_AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _vectors_by_id() -> dict[
    str, tuple[float, ...],
]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
    }


@lru_cache(maxsize=1)
def _families_by_id() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in candidate_families():
        for mid in f.member_ids:
            out[mid] = f.family_id
    return out


def _augmented_with(
    member_ids: tuple[str, ...],
    candidate: str,
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    cv = candidate_values_for_ids(
        candidate, member_ids,
    )
    return {
        mid: vecs[mid] + (cv[mid],)
        for mid in member_ids
        if mid in vecs
    }


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


@dataclass(frozen=True)
class AdaptiveOutcome:
    family_a: str
    family_b: str
    baseline_auc: float
    best_candidate: str
    best_auc: float
    rescued: bool
    candidate_aucs: tuple[
        tuple[str, float], ...,
    ]

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a": self.family_a,
            "family_b": self.family_b,
            "baseline_auc": self.baseline_auc,
            "best_candidate": self.best_candidate,
            "best_auc": self.best_auc,
            "rescued": self.rescued,
            "candidate_aucs": [
                {"candidate": c, "auc": a}
                for c, a in self.candidate_aucs
            ],
        }


@lru_cache(maxsize=1)
def all_adaptive_outcomes() -> tuple[
    AdaptiveOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[AdaptiveOutcome] = []
    for tr in all_transfer_outcomes():
        if tr.rescued:
            # Already rescued by v3.106; skip.
            out.append(AdaptiveOutcome(
                family_a=tr.family_a,
                family_b=tr.family_b,
                baseline_auc=tr.baseline_auc,
                best_candidate=(
                    "contradiction_type"
                ),
                best_auc=tr.injected_auc,
                rescued=True,
                candidate_aucs=(),
            ))
            continue
        a = fams_by_id.get(tr.family_a)
        b = fams_by_id.get(tr.family_b)
        if a is None or b is None:
            continue
        member_ids = tuple(
            sorted(set(a.member_ids + b.member_ids)),
        )
        per_cand: list[tuple[str, float]] = []
        for cand in ALL_CANDIDATES:
            vecs = _augmented_with(
                member_ids, cand,
            )
            per_cand.append(
                (cand, _pairwise_auc(vecs)),
            )
        # Pick best by (auc desc, name asc).
        per_cand_sorted = sorted(
            per_cand,
            key=lambda x: (-x[1], x[0]),
        )
        best_cand, best_auc = per_cand_sorted[0]
        rescued = best_auc >= _RESCUE_AUC_THRESHOLD
        out.append(AdaptiveOutcome(
            family_a=tr.family_a,
            family_b=tr.family_b,
            baseline_auc=tr.baseline_auc,
            best_candidate=(
                best_cand if rescued else ""
            ),
            best_auc=best_auc,
            rescued=rescued,
            candidate_aucs=tuple(per_cand),
        ))
    return tuple(out)


__all__ = [
    "AdaptiveOutcome",
    "all_adaptive_outcomes",
]
