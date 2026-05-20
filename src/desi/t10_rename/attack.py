"""v3.110 — apply each rename to the v3.107
adaptive search and measure AUC / purity
stability.

For each (kind, seed) cell we:

* rename every entangled-pair member id,
* compute the best candidate per instance using
  the renamed ids,
* aggregate mean AUC, mean purity, and the set
  of best-candidates picked.

Candidates whose mean AUC drops sharply across
rename seeds are flagged as ``broken``. The
``name_leakage_score`` is the proportion of
the v3.107 used_candidates that break under any
rename kind.
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
from ..t10_adaptive.adaptive import (
    ALL_CANDIDATES, adaptive_value,
)
from ..t10_adaptive.report import (
    used_candidates as v3107_used,
)
from ..t10_generalization.census import (
    candidate_families,
)
from ..t10_transfer.inject import (
    all_transfer_outcomes,
)
from .rename import (
    RENAME_KINDS, RENAME_SEEDS, rename_id,
)


_RESCUE_AUC_THRESHOLD: float = 0.70
_LEAKAGE_AUC_DROP: float = 0.20


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


def _augmented_renamed(
    member_ids: tuple[str, ...],
    candidate: str,
    kind: str, seed: int,
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    texts = _texts_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        rid = rename_id(mid, kind, seed)
        v = adaptive_value(
            candidate, rid, texts.get(mid, ""),
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


@dataclass(frozen=True)
class RenameCellOutcome:
    kind: str
    seed: int
    mean_auc: float
    rescue_rate: float
    best_candidate_distribution: tuple[
        tuple[str, int], ...,
    ]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "seed": self.seed,
            "mean_auc": self.mean_auc,
            "rescue_rate": self.rescue_rate,
            "best_candidate_distribution": [
                {"candidate": c, "count": n}
                for c, n in
                self.best_candidate_distribution
            ],
        }


@lru_cache(maxsize=1)
def all_rename_cell_outcomes() -> tuple[
    RenameCellOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[RenameCellOutcome] = []
    for kind in RENAME_KINDS:
        for seed in RENAME_SEEDS:
            aucs: list[float] = []
            cand_picks: list[str] = []
            rescued = 0
            for tr in all_transfer_outcomes():
                a = fams_by_id.get(tr.family_a)
                b = fams_by_id.get(tr.family_b)
                if a is None or b is None:
                    continue
                member_ids = tuple(
                    sorted(set(
                        a.member_ids
                        + b.member_ids,
                    )),
                )
                best_auc = 0.0
                best_cand = ""
                for cand in ALL_CANDIDATES:
                    vecs = _augmented_renamed(
                        member_ids, cand,
                        kind, seed,
                    )
                    auc = _pairwise_auc(vecs)
                    if auc > best_auc or (
                        auc == best_auc
                        and cand < best_cand
                    ):
                        best_auc = auc
                        best_cand = cand
                aucs.append(best_auc)
                if best_auc >= (
                    _RESCUE_AUC_THRESHOLD
                ):
                    rescued += 1
                    cand_picks.append(best_cand)
            from collections import Counter
            dist = sorted(
                Counter(cand_picks).items(),
                key=lambda x: (-x[1], x[0]),
            )
            out.append(RenameCellOutcome(
                kind=kind, seed=seed,
                mean_auc=(
                    _round(sum(aucs) / len(aucs))
                    if aucs else 0.0
                ),
                rescue_rate=(
                    _round(rescued / len(aucs))
                    if aucs else 0.0
                ),
                best_candidate_distribution=tuple(
                    dist,
                ),
            ))
    return tuple(out)


def rename_attack_auc() -> float:
    outs = all_rename_cell_outcomes()
    if not outs:
        return 0.0
    return _round(
        sum(o.mean_auc for o in outs) / len(outs),
    )


def rename_attack_rescue_rate() -> float:
    outs = all_rename_cell_outcomes()
    if not outs:
        return 0.0
    return _round(
        sum(o.rescue_rate for o in outs)
        / len(outs),
    )


def broken_candidates() -> tuple[str, ...]:
    """Candidates whose v3.107 selection no
    longer rescues under any rename seed
    (rescue rate drops below 0.10)."""
    outs = all_rename_cell_outcomes()
    used = set(v3107_used())
    broken: set[str] = set()
    for cand in used:
        # rescue rate (per cell) when cand is the
        # forced best - approximated by checking
        # whether cand still appears in any
        # cell's distribution.
        for o in outs:
            counts = dict(
                o.best_candidate_distribution,
            )
            if counts.get(cand, 0) == 0:
                # cand was preferred 0 times in
                # this cell; one strike.
                continue
        # Simpler: mean AUC across cells for
        # this candidate alone (use the dist
        # weight).
    # Direct measure: a used_candidate is broken
    # if its share of best picks falls below
    # 0.05 in EVERY rename cell.
    for cand in used:
        always_low = True
        for o in outs:
            counts = dict(
                o.best_candidate_distribution,
            )
            total = sum(counts.values()) or 1
            share = counts.get(cand, 0) / total
            if share >= 0.05:
                always_low = False
                break
        if always_low:
            broken.add(cand)
    return tuple(sorted(broken))


def name_leakage_score() -> float:
    used = v3107_used()
    if not used:
        return 0.0
    return _round(len(broken_candidates()) / len(used))


__all__ = [
    "RenameCellOutcome",
    "all_rename_cell_outcomes",
    "broken_candidates",
    "name_leakage_score",
    "rename_attack_auc",
    "rename_attack_rescue_rate",
]
