"""v3.59 — content-only pair resonance probe.

Replays the v3.50 + v3.54 pair resonance analysis
using only the 5-d content subspace
(CONTENT_DIMS = frame_id, novelty, anchor_density,
contradiction_load, source_quality) from v3.57.
Reports both the global aggregate and the per-corpus
result.

Probe radius is chosen inside the content-space
discrimination band: r=2.0 produces the only non-zero
global resonant_pair_count (8 pairs); radii above
2.0 collapse coverage to saturation, radii below
collapse to 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..cause_aware_control.controller import control_all
from ..content_method.features import content_vector
from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA, corpus_leakage_trajectories,
    corpus_plateau_anchors, corpus_present,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import euclidean


CONTENT_PROBE_RADIUS: float = 2.0
MIN_ANCHORS_FOR_PAIRS: int = 2
GLOBAL_CONTROL_COUNT: int = 20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


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
class ContentPairSummary:
    scope: str
    cohort: str
    anchor_count: int
    leakage_count: int
    pair_count: int
    resonant_pair_count: int
    subadditivity_score: float
    mean_union_size: float
    max_union_size: int

    def to_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
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


def _summarise(
    scope: str, cohort: str,
    anchors_vecs: list[tuple[str, tuple[float, ...]]],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> ContentPairSummary:
    if not anchors_vecs:
        return ContentPairSummary(
            scope=scope, cohort=cohort,
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
    return ContentPairSummary(
        scope=scope, cohort=cohort,
        anchor_count=len(anchors_vecs),
        leakage_count=len(leakage_vecs),
        pair_count=len(pairs),
        resonant_pair_count=n_resonant,
        subadditivity_score=sub,
        mean_union_size=mean_u,
        max_union_size=max(unions, default=0),
    )


def _trajectory_by_id() -> dict:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def _stride_sample(
    sorted_ids: tuple[str, ...], n: int,
) -> tuple[str, ...]:
    if not sorted_ids or n <= 0:
        return ()
    if n >= len(sorted_ids):
        return sorted_ids
    stride = max(1, len(sorted_ids) // n)
    return tuple(sorted_ids[i * stride] for i in range(n))


def global_plateau_summary(
    radius: float = CONTENT_PROBE_RADIUS,
) -> ContentPairSummary:
    plats = list(collect_plateau_anchors())
    leaks = list(collect_leakage_trajectories())
    anchors_vecs = [
        (t.trajectory_id, content_vector(t.states))
        for t in plats
    ]
    leakage_vecs = [
        content_vector(t.states) for t in leaks
    ]
    return _summarise(
        "global", "plateau", anchors_vecs,
        leakage_vecs, radius,
    )


def global_control_summary(
    radius: float = CONTENT_PROBE_RADIUS,
) -> ContentPairSummary:
    leaks = list(collect_leakage_trajectories())
    leakage_vecs = [
        content_vector(t.states) for t in leaks
    ]
    rescued_ids = sorted(
        o.trajectory_id for o in control_all()
        if o.rescued
    )
    ctrl_ids = _stride_sample(
        tuple(rescued_ids), GLOBAL_CONTROL_COUNT,
    )
    trajs = _trajectory_by_id()
    anchors_vecs = [
        (cid, content_vector(trajs[cid].states))
        for cid in ctrl_ids if cid in trajs
    ]
    return _summarise(
        "global", "control", anchors_vecs,
        leakage_vecs, radius,
    )


def per_corpus_plateau_summary(
    corpus: str,
    radius: float = CONTENT_PROBE_RADIUS,
) -> ContentPairSummary:
    plats = list(corpus_plateau_anchors(corpus))
    leaks = list(corpus_leakage_trajectories(corpus))
    anchors_vecs = [
        (t.trajectory_id, content_vector(t.states))
        for t in plats
    ]
    leakage_vecs = [
        content_vector(t.states) for t in leaks
    ]
    return _summarise(
        corpus, "plateau", anchors_vecs,
        leakage_vecs, radius,
    )


def per_corpus_control_summary(
    corpus: str,
    radius: float = CONTENT_PROBE_RADIUS,
) -> ContentPairSummary:
    plats = corpus_plateau_anchors(corpus)
    n = max(MIN_ANCHORS_FOR_PAIRS, len(plats))
    corpus_ids = {
        t.trajectory_id
        for t in extract_all_trajectories()
        if t.trajectory_id.split(":", 1)[0]
            .split("-")[0] == corpus
    }
    rescued = sorted(
        o.trajectory_id for o in control_all()
        if o.rescued and o.trajectory_id in corpus_ids
    )
    ctrl_ids = _stride_sample(tuple(rescued), n)
    trajs = _trajectory_by_id()
    anchors_vecs = [
        (cid, content_vector(trajs[cid].states))
        for cid in ctrl_ids if cid in trajs
    ]
    leaks = list(corpus_leakage_trajectories(corpus))
    leakage_vecs = [
        content_vector(t.states) for t in leaks
    ]
    return _summarise(
        corpus, "control", anchors_vecs,
        leakage_vecs, radius,
    )


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
    "CONTENT_PROBE_RADIUS", "ContentPairSummary",
    "GLOBAL_CONTROL_COUNT",
    "MIN_ANCHORS_FOR_PAIRS",
    "eligible_corpora", "global_control_summary",
    "global_plateau_summary", "ineligible_corpora",
    "per_corpus_control_summary",
    "per_corpus_plateau_summary",
]
