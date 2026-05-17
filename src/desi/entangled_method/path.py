"""v3.95 — temporal separability.

Given each anchor's per-dim rise-index vector, can
we tell G_v316susp apart from E_v317h?

We compute pairwise Hamming distance on the rise-
index vectors, score = -distance, label =
same_family, and report the ROC AUC. If the AUC is
near 0.5 the two families have the same temporal
method.
"""
from __future__ import annotations

import itertools

from .method import all_method_signatures


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _hamming(
    a: tuple[int, ...], b: tuple[int, ...],
) -> int:
    return sum(
        1 for x, y in zip(a, b) if x != y
    )


def temporal_pair_scores() -> tuple[
    tuple[str, str, int, bool], ...,
]:
    sigs = all_method_signatures()
    out: list[tuple[str, str, int, bool]] = []
    for a, b in itertools.combinations(sigs, 2):
        d = _hamming(a.rise_index, b.rise_index)
        out.append((
            a.trajectory_id, b.trajectory_id,
            d, a.family_id == b.family_id,
        ))
    return tuple(out)


def temporal_separability() -> float:
    """ROC AUC of -hamming_distance against the
    same-family label. 0.5 = method-doppelganger
    (no temporal split); 1.0 = fully separable."""
    pairs = temporal_pair_scores()
    pos = [-d for _, _, d, same in pairs if same]
    neg = [
        -d for _, _, d, same in pairs if not same
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
    total = len(pos) * len(neg)
    return _round((wins + 0.5 * ties) / total)


def temporal_pair_count() -> int:
    return len(temporal_pair_scores())


def temporal_same_family_pair_count() -> int:
    return sum(
        1 for _, _, _, same in temporal_pair_scores()
        if same
    )


def temporal_cross_family_pair_count() -> int:
    return sum(
        1 for _, _, _, same in temporal_pair_scores()
        if not same
    )


__all__ = [
    "temporal_cross_family_pair_count",
    "temporal_pair_count",
    "temporal_pair_scores",
    "temporal_same_family_pair_count",
    "temporal_separability",
]
