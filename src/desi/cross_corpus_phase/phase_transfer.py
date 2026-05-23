"""v3.56 — phase transfer aggregation.

A corpus's phase curve "transfers" iff its
discontinuity_score is strictly positive (matches the
v3.52 PASS condition). Eligibility requires at least
MIN_ANCHORS_FOR_DISCONTINUITY plateau anchors.
"""
from __future__ import annotations

from .transition import (
    coupling_strength, discontinuity_score,
    eligible_corpora, per_corpus_phase_curve,
    saturation_point,
)


def transfers_at(corpus: str) -> bool:
    return discontinuity_score(
        per_corpus_phase_curve(corpus),
    ) > 0


def transfer_rate() -> float:
    eligible = eligible_corpora()
    if not eligible:
        return 0.0
    return round(
        sum(
            1 for c in eligible if transfers_at(c)
        ) / len(eligible),
        6,
    )


def per_corpus_summary(
    corpus: str,
) -> dict[str, object]:
    curve = per_corpus_phase_curve(corpus)
    return {
        "corpus": corpus,
        "phase_curve": [p.to_dict() for p in curve],
        "discontinuity_score":
            discontinuity_score(curve),
        "saturation_point": saturation_point(curve),
        "coupling_strength":
            coupling_strength(curve),
    }


__all__ = [
    "per_corpus_summary", "transfer_rate",
    "transfers_at",
]
