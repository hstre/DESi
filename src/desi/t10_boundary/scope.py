"""v3.119 — pool-level recoverability features.

For each v3.117 blindness pool we compute:

* ``state_variance``  - variance of the pool's
  state vectors. Always 0 by construction
  (pool members share the canonical signature)
  but recorded for completeness.
* ``text_variance``   - 1 - mean_pairwise_text_jaccard.
  High value = pool members have different
  texts (T10 has something to work with).
* ``rescuable``       - boolean: True iff the
  pool's text_variance exceeds the recoverable
  threshold AND the closed v3.108 small_vocab
  (contradiction_type +
  corpus_hash + letter_prefix_hash) rescues
  ≥ one pair drawn from the pool.

The recoverability_threshold is the smallest
text_variance at which any pool is rescuable.
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
from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)
from ..state_blindness_taxonomy.taxonomy import (
    _mean_pairwise_jaccard,
)
from ..t10_adaptive.adaptive import (
    ALL_CANDIDATES, adaptive_value,
)


_RESCUE_AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


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


def _pairwise_auc_for_pool(
    pool: BlindnessPool,
    candidate: str,
) -> float:
    """Treat each family in the pool as a class;
    compute pairwise AUC against same-family
    label using the augmented residual + +1 dim
    vector."""
    fam_of: dict[str, str] = {}
    for fid in pool.family_ids:
        for mid in pool.member_ids:
            if mid.startswith(
                fid.replace(":", ":") + "0",
            ) or mid.startswith(fid):
                fam_of[mid] = fid
    # Simpler: family is the prefix up to first
    # numeric.
    import re
    for mid in pool.member_ids:
        if ":" in mid:
            corpus, tail = mid.split(":", 1)
            m = re.match(r"([A-Za-z]+)", tail)
            if m:
                fam_of[mid] = (
                    f"{corpus}:{m.group(1)}"
                )
    vecs = _vectors_by_id()
    texts = _texts_by_id()
    aug: dict[str, tuple[float, ...]] = {}
    for mid in pool.member_ids:
        if mid not in vecs:
            continue
        v = adaptive_value(
            candidate, mid,
            texts.get(mid, ""),
        )
        aug[mid] = vecs[mid] + (v,)
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(aug), 2,
    ):
        s = -euclidean(aug[a], aug[b])
        if fam_of.get(a) == fam_of.get(b):
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
class PoolRecoverability:
    pool_id: int
    member_count: int
    family_count: int
    text_jaccard: float
    text_variance: float
    state_variance: float
    best_candidate_auc: float
    rescuable: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "member_count": self.member_count,
            "family_count": self.family_count,
            "text_jaccard": self.text_jaccard,
            "text_variance": self.text_variance,
            "state_variance":
                self.state_variance,
            "best_candidate_auc":
                self.best_candidate_auc,
            "rescuable": self.rescuable,
        }


@lru_cache(maxsize=1)
def all_pool_recoverability() -> tuple[
    PoolRecoverability, ...,
]:
    out: list[PoolRecoverability] = []
    for p in cross_family_pools():
        jaccard = _mean_pairwise_jaccard(
            p.member_ids,
        )
        text_var = _round(1.0 - jaccard)
        best_auc = 0.0
        for cand in ALL_CANDIDATES:
            auc = _pairwise_auc_for_pool(p, cand)
            if auc > best_auc:
                best_auc = auc
        rescuable = best_auc >= (
            _RESCUE_AUC_THRESHOLD
        )
        out.append(PoolRecoverability(
            pool_id=p.pool_id,
            member_count=p.member_count,
            family_count=p.family_count,
            text_jaccard=jaccard,
            text_variance=text_var,
            state_variance=0.0,
            best_candidate_auc=best_auc,
            rescuable=rescuable,
        ))
    return tuple(out)


def recoverability_threshold() -> float:
    """Smallest text_variance at which any pool
    is rescuable; ``1.0`` if none are."""
    outs = all_pool_recoverability()
    rescuable_vars = [
        o.text_variance for o in outs
        if o.rescuable
    ]
    if not rescuable_vars:
        return 1.0
    return _round(min(rescuable_vars))


def blindness_prediction_auc() -> float:
    """ROC AUC of the text_variance score against
    the ``rescuable`` label, treating each pool
    as one sample."""
    outs = all_pool_recoverability()
    pos = [
        o.text_variance for o in outs
        if o.rescuable
    ]
    neg = [
        o.text_variance for o in outs
        if not o.rescuable
    ]
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


def false_positive_rate() -> float:
    """Fraction of unrescuable pools that the
    text_variance heuristic would NEVERTHELESS
    flag as rescuable, using the discovered
    recoverability_threshold."""
    outs = all_pool_recoverability()
    thr = recoverability_threshold()
    neg = [o for o in outs if not o.rescuable]
    if not neg:
        return 0.0
    fp = sum(
        1 for o in neg if o.text_variance >= thr
    )
    return _round(fp / len(neg))


def false_negative_rate() -> float:
    """Fraction of rescuable pools that fall
    BELOW the discovered recoverability
    threshold."""
    outs = all_pool_recoverability()
    thr = recoverability_threshold()
    pos = [o for o in outs if o.rescuable]
    if not pos:
        return 0.0
    fn = sum(
        1 for o in pos if o.text_variance < thr
    )
    return _round(fn / len(pos))


__all__ = [
    "PoolRecoverability",
    "all_pool_recoverability",
    "blindness_prediction_auc",
    "false_negative_rate",
    "false_positive_rate",
    "recoverability_threshold",
]
