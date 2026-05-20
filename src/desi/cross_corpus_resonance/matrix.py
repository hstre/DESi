"""v3.54 — per-corpus pair matrix.

Convenience accessor that returns each eligible
corpus's plateau anchor pair matrix (|A∪B|) at the
v3.54 probe radius. Single-anchor corpora yield a
1x1 matrix containing only the self-coverage; zero-
anchor corpora yield an empty dict.
"""
from __future__ import annotations

from ..cross_corpus.corpus_loader import (
    REFERENCE_CORPORA, corpus_plateau_anchors,
    corpus_leakage_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from .pair_transfer import PROBE_RADIUS, _coverage_set


def per_corpus_pair_matrix(
    corpus: str, radius: float = PROBE_RADIUS,
) -> dict[str, dict[str, int]]:
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
    ids = sorted(coverages.keys())
    out: dict[str, dict[str, int]] = {}
    for a in ids:
        row: dict[str, int] = {}
        for b in ids:
            row[b] = len(coverages[a] | coverages[b])
        out[a] = row
    return out


def all_corpora_pair_matrices(
    radius: float = PROBE_RADIUS,
) -> dict[str, dict[str, dict[str, int]]]:
    return {
        c: per_corpus_pair_matrix(c, radius)
        for c in REFERENCE_CORPORA
    }


__all__ = [
    "all_corpora_pair_matrices",
    "per_corpus_pair_matrix",
]
