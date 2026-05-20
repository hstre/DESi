"""v3.56 — per-corpus phase curve construction.

For each reference corpus, walk the closed mass set
{0, 1, 2, 3, 4, 8} plus the corpus's anchor-count
saturation point. Compute leakage_count per k under
the v3.52 union-of-balls policy at PROBE_RADIUS=3.5.

Corpora with fewer than MIN_ANCHORS_FOR_DISCONTINUITY
plateau anchors cannot exhibit a discontinuity by
construction (a single-anchor curve is flat from k=1
onward) and are recorded as ineligible.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA, corpus_leakage_trajectories,
    corpus_plateau_anchors, corpus_present,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..semantic_phase_transition.mass import (
    MASS_LEVELS, SATURATION_MASS,
)


PROBE_RADIUS: float = 3.5
MIN_ANCHORS_FOR_DISCONTINUITY: int = 2


@dataclass(frozen=True)
class PhasePoint:
    mass_level: int
    leakage_count: int
    additive_prediction: int

    def to_dict(self) -> dict[str, object]:
        return {
            "mass_level": self.mass_level,
            "leakage_count": self.leakage_count,
            "additive_prediction":
                self.additive_prediction,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _ordered_anchor_ids(corpus: str) -> tuple[str, ...]:
    return tuple(sorted(
        t.trajectory_id
        for t in corpus_plateau_anchors(corpus)
    ))


def per_corpus_phase_curve(
    corpus: str, radius: float = PROBE_RADIUS,
) -> tuple[PhasePoint, ...]:
    plats = list(corpus_plateau_anchors(corpus))
    leaks = list(corpus_leakage_trajectories(corpus))
    sorted_plats = sorted(
        plats, key=lambda t: t.trajectory_id,
    )
    leak_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    coverages: dict[str, frozenset[int]] = {}
    for t in sorted_plats:
        av = trajectory_vector(t.states)
        coverages[t.trajectory_id] = frozenset(
            i for i, lv in enumerate(leak_vecs)
            if euclidean(av, lv) <= radius
        )
    # k_values = the directive's closed mass set
    # PLUS the corpus's anchor count for saturation.
    levels = list(MASS_LEVELS)
    sat = len(plats)
    if sat not in levels:
        levels.append(sat)
    if SATURATION_MASS not in levels:
        levels.append(SATURATION_MASS)
    levels = sorted(set(levels))
    sorted_ids = [
        t.trajectory_id for t in sorted_plats
    ]
    out: list[PhasePoint] = []
    for k in levels:
        if k > len(sorted_ids):
            k = len(sorted_ids)
        ids = sorted_ids[:k]
        cum: set[int] = set()
        additive = 0
        for aid in ids:
            cum |= coverages[aid]
            additive += len(coverages[aid])
        out.append(PhasePoint(
            mass_level=k,
            leakage_count=len(cum),
            additive_prediction=additive,
        ))
    # de-dup by mass_level (clipping may produce
    # duplicates when k > num_anchors)
    seen: set[int] = set()
    deduped: list[PhasePoint] = []
    for p in out:
        if p.mass_level in seen:
            continue
        seen.add(p.mass_level)
        deduped.append(p)
    return tuple(deduped)


def discontinuity_score(
    curve: tuple[PhasePoint, ...],
) -> float:
    if len(curve) < 2:
        return 0.0
    max_leak = max(p.leakage_count for p in curve)
    if max_leak == 0:
        return 0.0
    deltas = [
        abs(curve[i + 1].leakage_count
            - curve[i].leakage_count)
        for i in range(len(curve) - 1)
    ]
    return _round(max(deltas) / max_leak)


def saturation_point(
    curve: tuple[PhasePoint, ...],
) -> int | None:
    if not curve:
        return None
    max_leak = max(p.leakage_count for p in curve)
    if max_leak == 0:
        return None
    for p in curve:
        if p.leakage_count >= max_leak:
            return p.mass_level
    return None


def coupling_strength(
    curve: tuple[PhasePoint, ...],
) -> float:
    sum_leak = sum(
        p.leakage_count for p in curve
        if p.additive_prediction > 0
    )
    sum_add = sum(
        p.additive_prediction for p in curve
        if p.additive_prediction > 0
    )
    if sum_add == 0:
        return 0.0
    return _round(1.0 - sum_leak / sum_add)


def eligible_corpora() -> tuple[str, ...]:
    return tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
        and len(corpus_plateau_anchors(c))
            >= MIN_ANCHORS_FOR_DISCONTINUITY
    )


def ineligible_corpora() -> tuple[str, ...]:
    return tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
        and len(corpus_plateau_anchors(c))
            < MIN_ANCHORS_FOR_DISCONTINUITY
    )


__all__ = [
    "MIN_ANCHORS_FOR_DISCONTINUITY", "PROBE_RADIUS",
    "PhasePoint", "coupling_strength",
    "discontinuity_score", "eligible_corpora",
    "ineligible_corpora",
    "per_corpus_phase_curve",
    "saturation_point",
]
