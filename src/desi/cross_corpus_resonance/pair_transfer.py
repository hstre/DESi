"""v3.54 — per-corpus pair resonance analysis.

For each reference corpus, compute the v3.50-style
plateau pair matrix using ONLY that corpus's plateau
anchors and its leakage cohort. Same probe radius
(3.5) as v3.50.

Corpora with fewer than two plateau anchors are
ineligible for pair analysis; they are recorded in
the report's ``ineligible_corpora`` field but excluded
from the pair_transfer_rate denominator.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..cause_aware_control.controller import control_all
from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA,
    corpus_leakage_trajectories,
    corpus_plateau_anchors,
    corpus_present, corpus_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5
MIN_ANCHORS_FOR_PAIRS: int = 2


def _coverage_set(
    anchor_vec: tuple[float, ...],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> frozenset[int]:
    return frozenset(
        i for i, lv in enumerate(leakage_vecs)
        if euclidean(anchor_vec, lv) <= radius
    )


def _is_resonant(
    a: frozenset, b: frozenset,
) -> bool:
    if not a or not b:
        return False
    return not (a <= b or b <= a)


@dataclass(frozen=True)
class CorpusPairSummary:
    corpus: str
    cohort: str          # "plateau" | "control"
    anchor_count: int
    leakage_count: int
    pair_count: int
    resonant_pair_count: int
    subadditivity_score: float
    mean_union_size: float
    max_union_size: int

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus": self.corpus,
            "cohort": self.cohort,
            "anchor_count": self.anchor_count,
            "leakage_count": self.leakage_count,
            "pair_count": self.pair_count,
            "resonant_pair_count":
                self.resonant_pair_count,
            "subadditivity_score":
                self.subadditivity_score,
            "mean_union_size":
                self.mean_union_size,
            "max_union_size": self.max_union_size,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _summarise(
    corpus: str, cohort: str,
    anchors_vecs: list[tuple[str, tuple[float, ...]]],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> CorpusPairSummary:
    if not anchors_vecs:
        return CorpusPairSummary(
            corpus=corpus, cohort=cohort,
            anchor_count=0,
            leakage_count=len(leakage_vecs),
            pair_count=0, resonant_pair_count=0,
            subadditivity_score=0.0,
            mean_union_size=0.0, max_union_size=0,
        )
    coverages = {
        aid: _coverage_set(av, leakage_vecs, radius)
        for aid, av in anchors_vecs
    }
    pairs = list(
        combinations(sorted(coverages.keys()), 2),
    )
    n_resonant = 0
    sum_additive = 0
    sum_overlap = 0
    unions: list[int] = []
    for a, b in pairs:
        ca, cb = coverages[a], coverages[b]
        u = ca | cb
        if _is_resonant(ca, cb):
            n_resonant += 1
        sum_additive += len(ca) + len(cb)
        sum_overlap += len(ca) + len(cb) - len(u)
        unions.append(len(u))
    sub = (
        _round(sum_overlap / sum_additive)
        if sum_additive > 0 else 0.0
    )
    mean_u = (
        _round(sum(unions) / len(unions))
        if unions else 0.0
    )
    return CorpusPairSummary(
        corpus=corpus, cohort=cohort,
        anchor_count=len(anchors_vecs),
        leakage_count=len(leakage_vecs),
        pair_count=len(pairs),
        resonant_pair_count=n_resonant,
        subadditivity_score=sub,
        mean_union_size=mean_u,
        max_union_size=max(unions, default=0),
    )


def _per_corpus_control_anchor_ids(
    corpus: str, n: int,
) -> tuple[str, ...]:
    """Deterministic control anchors from the corpus's
    own non-plateau, non-leakage SUPPORTED trajectories
    that the controller rescued. If the corpus has too
    few rescued ids, fall back to whatever rescued
    trajectories exist (still corpus-local)."""
    corpus_ids = {
        t.trajectory_id
        for t in corpus_trajectories(corpus)
    }
    rescued = sorted(
        o.trajectory_id for o in control_all()
        if o.rescued and o.trajectory_id in corpus_ids
    )
    if not rescued:
        return ()
    if n >= len(rescued):
        return tuple(rescued)
    stride = max(1, len(rescued) // n)
    return tuple(
        rescued[i * stride] for i in range(n)
    )


def per_corpus_plateau_summary(
    corpus: str, radius: float = PROBE_RADIUS,
) -> CorpusPairSummary:
    plats = list(corpus_plateau_anchors(corpus))
    leaks = list(corpus_leakage_trajectories(corpus))
    anchors_vecs = [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in plats
    ]
    leakage_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    return _summarise(
        corpus, "plateau", anchors_vecs,
        leakage_vecs, radius,
    )


def per_corpus_control_summary(
    corpus: str, radius: float = PROBE_RADIUS,
) -> CorpusPairSummary:
    plats = corpus_plateau_anchors(corpus)
    n = max(MIN_ANCHORS_FOR_PAIRS, len(plats))
    ctrl_ids = _per_corpus_control_anchor_ids(corpus, n)
    by_id = {
        t.trajectory_id: t
        for t in corpus_trajectories(corpus)
    }
    anchors_vecs = [
        (cid, trajectory_vector(by_id[cid].states))
        for cid in ctrl_ids if cid in by_id
    ]
    leaks = list(corpus_leakage_trajectories(corpus))
    leakage_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    return _summarise(
        corpus, "control", anchors_vecs,
        leakage_vecs, radius,
    )


def triple_max_extra(
    corpus: str, radius: float = PROBE_RADIUS,
) -> int:
    plats = list(corpus_plateau_anchors(corpus))
    if len(plats) < 3:
        return 0
    leaks = list(corpus_leakage_trajectories(corpus))
    leakage_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    coverages = {
        t.trajectory_id: _coverage_set(
            trajectory_vector(t.states),
            leakage_vecs, radius,
        )
        for t in plats
    }
    out_max = 0
    ids = sorted(coverages.keys())
    for a, b, c in combinations(ids, 3):
        ca, cb, cc = (
            coverages[a], coverages[b], coverages[c],
        )
        union3 = ca | cb | cc
        pair_max = max(
            len(ca | cb), len(ca | cc), len(cb | cc),
        )
        extra = len(union3) - pair_max
        if extra > out_max:
            out_max = extra
    return out_max


def eligible_corpora() -> tuple[str, ...]:
    return tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
        and len(corpus_plateau_anchors(c))
            >= MIN_ANCHORS_FOR_PAIRS
    )


def ineligible_corpora() -> tuple[str, ...]:
    return tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
        and len(corpus_plateau_anchors(c))
            < MIN_ANCHORS_FOR_PAIRS
    )


__all__ = [
    "CorpusPairSummary", "MIN_ANCHORS_FOR_PAIRS",
    "PROBE_RADIUS", "eligible_corpora",
    "ineligible_corpora",
    "per_corpus_control_summary",
    "per_corpus_plateau_summary",
    "triple_max_extra",
]
