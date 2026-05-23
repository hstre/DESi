"""v3.55 — per-corpus anti-anchor suppression.

Replays the v3.51 leakage-sample anti-anchor probe
inside each reference corpus. Anti-anchors are drawn
from the corpus's own leakage cohort via the v3.51
deterministic stride sampling; if the corpus has
fewer than ANTI_COUNT leakages the entire leakage
cohort is used as the anti set.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..anti_anchor.anchors import (
    ANTI_COUNT, ANTI_RADIUS,
)
from ..anti_anchor.ablation import PLATEAU_RADIUS
from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA, corpus_leakage_trajectories,
    corpus_plateau_anchors, corpus_present,
)
from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)


def _stride_sample(
    sorted_ids: tuple[str, ...], n: int,
) -> tuple[str, ...]:
    if not sorted_ids or n <= 0:
        return ()
    if n >= len(sorted_ids):
        return sorted_ids
    stride = max(1, len(sorted_ids) // n)
    return tuple(sorted_ids[i * stride] for i in range(n))


def per_corpus_anti_ids(
    corpus: str, n: int = ANTI_COUNT,
) -> tuple[str, ...]:
    ids = sorted(
        t.trajectory_id
        for t in corpus_leakage_trajectories(corpus)
    )
    return _stride_sample(tuple(ids), n)


@dataclass(frozen=True)
class CorpusSuppressionRecord:
    corpus: str
    plateau_count: int
    leakage_count: int
    anti_count: int
    baseline_leakage: int
    leakage_after_anti: int
    plateau_recall: float
    suppression_fraction: float
    repulsion_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus": self.corpus,
            "plateau_count": self.plateau_count,
            "leakage_count": self.leakage_count,
            "anti_count": self.anti_count,
            "baseline_leakage":
                self.baseline_leakage,
            "leakage_after_anti":
                self.leakage_after_anti,
            "plateau_recall": self.plateau_recall,
            "suppression_fraction":
                self.suppression_fraction,
            "repulsion_count": self.repulsion_count,
        }


def per_corpus_suppression(
    corpus: str,
) -> CorpusSuppressionRecord:
    plats = list(corpus_plateau_anchors(corpus))
    leaks = list(corpus_leakage_trajectories(corpus))
    plat_vecs = tuple(
        trajectory_vector(t.states) for t in plats
    )
    anti_ids = set(per_corpus_anti_ids(corpus))
    anti_vecs = tuple(
        trajectory_vector(t.states) for t in leaks
        if t.trajectory_id in anti_ids
    )
    if not plat_vecs or not leaks:
        return CorpusSuppressionRecord(
            corpus=corpus, plateau_count=len(plats),
            leakage_count=len(leaks),
            anti_count=len(anti_vecs),
            baseline_leakage=0,
            leakage_after_anti=0, plateau_recall=0.0,
            suppression_fraction=0.0,
            repulsion_count=0,
        )
    baseline = 0
    leak_after = 0
    repelled = 0
    for t in leaks:
        v = trajectory_vector(t.states)
        near_plat = (
            manifold_distance(v, plat_vecs)[0]
            <= PLATEAU_RADIUS
        )
        if not near_plat:
            continue
        baseline += 1
        if anti_vecs:
            near_anti = (
                manifold_distance(v, anti_vecs)[0]
                <= ANTI_RADIUS
            )
        else:
            near_anti = False
        if near_anti:
            repelled += 1
        else:
            leak_after += 1
    captured = 0
    for t in plats:
        v = trajectory_vector(t.states)
        near_plat = (
            manifold_distance(v, plat_vecs)[0]
            <= PLATEAU_RADIUS
        )
        if not near_plat:
            continue
        if anti_vecs:
            near_anti = (
                manifold_distance(v, anti_vecs)[0]
                <= ANTI_RADIUS
            )
        else:
            near_anti = False
        if not near_anti:
            captured += 1
    recall = (
        round(captured / len(plats), 6)
        if plats else 0.0
    )
    suppression = (
        round(1.0 - leak_after / baseline, 6)
        if baseline > 0 else 0.0
    )
    return CorpusSuppressionRecord(
        corpus=corpus, plateau_count=len(plats),
        leakage_count=len(leaks),
        anti_count=len(anti_vecs),
        baseline_leakage=baseline,
        leakage_after_anti=leak_after,
        plateau_recall=recall,
        suppression_fraction=suppression,
        repulsion_count=repelled,
    )


def all_corpus_suppression_records(
) -> tuple[CorpusSuppressionRecord, ...]:
    return tuple(
        per_corpus_suppression(c)
        for c in REFERENCE_CORPORA
        if corpus_present(c)
    )


__all__ = [
    "ANTI_COUNT", "ANTI_RADIUS", "PLATEAU_RADIUS",
    "CorpusSuppressionRecord",
    "all_corpus_suppression_records",
    "per_corpus_anti_ids", "per_corpus_suppression",
]
