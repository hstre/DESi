"""v3.60 — per-corpus crossed transfer.

Within each eligible corpus, classify every plateau
pair by the v3.57 cluster lookup and check whether
any condition produces resonance. The
``crossed_transfer_rate`` aggregates: a corpus
"transfers" iff at least one non-empty condition
has resonant_pair_count > 0.
"""
from __future__ import annotations

from itertools import combinations

from ..content_method.decompose import (
    cluster_assignments, cohort_features,
)
from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA, corpus_leakage_trajectories,
    corpus_plateau_anchors, corpus_present,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from .conditions import (
    CROSSED_PROBE_RADIUS, _classify, _coverage_set,
    _is_resonant,
)


MIN_ANCHORS_FOR_PAIRS: int = 2


def eligible_corpora() -> tuple[str, ...]:
    return tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
        and len(corpus_plateau_anchors(c))
            >= MIN_ANCHORS_FOR_PAIRS
    )


def _cluster_lookup_for_plateau(
) -> tuple[dict[str, int], dict[str, int]]:
    feats = cohort_features()
    c = cluster_assignments("content")
    m = cluster_assignments("method")
    content = {
        f.trajectory_id: c[i]
        for i, f in enumerate(feats)
        if f.cohort == "plateau"
    }
    method = {
        f.trajectory_id: m[i]
        for i, f in enumerate(feats)
        if f.cohort == "plateau"
    }
    return content, method


def corpus_resonance_by_condition(
    corpus: str,
    radius: float = CROSSED_PROBE_RADIUS,
) -> dict[str, int]:
    content, method = _cluster_lookup_for_plateau()
    plats = list(corpus_plateau_anchors(corpus))
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
    out: dict[str, int] = {}
    ids = sorted(coverages.keys())
    for a, b in combinations(ids, 2):
        ca, cb = coverages[a], coverages[b]
        if a not in content or b not in content:
            continue
        same_c = content[a] == content[b]
        same_m = method[a] == method[b]
        cond = _classify(same_c, same_m)
        if _is_resonant(ca, cb):
            out[cond] = out.get(cond, 0) + 1
    return out


def crossed_transfer_rate(
    radius: float = CROSSED_PROBE_RADIUS,
) -> float:
    """Fraction of eligible corpora in which at least
    one cross-condition cell shows a resonant pair."""
    eligible = eligible_corpora()
    if not eligible:
        return 0.0
    transferred = sum(
        1 for c in eligible
        if any(
            v > 0 for v in
            corpus_resonance_by_condition(c, radius).values()
        )
    )
    return round(transferred / len(eligible), 6)


__all__ = [
    "MIN_ANCHORS_FOR_PAIRS",
    "corpus_resonance_by_condition",
    "crossed_transfer_rate", "eligible_corpora",
]
