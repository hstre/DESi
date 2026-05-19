"""v7.1 — polarisation / coherence metrics.

``identity_bias`` measures whether the
classifier's certainty correlates with tribe
membership BEYOND what intrinsic quality
explains. We compute it as the residual standard
deviation of mean-certainty-per-tribe after
subtracting mean-quality-per-tribe.

``polarization_resistance`` is 1 - identity_bias
(clamped). ``coherence_score`` is the fraction
of within-tribe certainty pairs that AGREE
(both HIGH/HIGH or both LOW/LOW or both
MEDIUM/MEDIUM).
"""
from __future__ import annotations

import math

from .identity import (
    classified_claims,
    mean_certainty_score_per_tribe,
    mean_quality_per_tribe,
)
from .tribes import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def identity_bias() -> float:
    """Residual std-dev of mean-certainty per
    tribe AFTER controlling for mean-quality.
    Zero iff certainty is a pure function of
    quality."""
    cert = mean_certainty_score_per_tribe()
    qual = mean_quality_per_tribe()
    if not cert:
        return 0.0
    residuals = [
        cert[t] - qual[t]
        for t in cert
    ]
    mean_r = sum(residuals) / len(residuals)
    var = sum(
        (r - mean_r) ** 2 for r in residuals
    ) / len(residuals)
    return _round(math.sqrt(var))


def polarization_resistance() -> float:
    return _round(
        max(0.0, 1.0 - 2.0 * identity_bias()),
    )


def coherence_score() -> float:
    """Classifier monotonicity across ALL pairs:
    higher epistemic_quality must NEVER receive
    lower certainty. A pair coheres if the
    certainty ordering matches the quality
    ordering (ties allowed in either direction).
    If the classifier ever lets a low-quality
    claim out-rank a high-quality claim because
    of tribal identity, this metric drops below
    1.0."""
    score_map = {
        "high": 2, "medium": 1, "low": 0,
    }
    claims = classified_claims()
    total = 0
    cohere = 0
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            total += 1
            a, b = claims[i], claims[j]
            qa = a.epistemic_quality
            qb = b.epistemic_quality
            ca = score_map[a.certainty]
            cb = score_map[b.certainty]
            if qa > qb and ca < cb:
                continue
            if qb > qa and cb < ca:
                continue
            cohere += 1
    if total == 0:
        return 1.0
    return _round(cohere / total)


def governance_integrity() -> float:
    """The classifier MUST emit a closed
    Certainty value for every claim - any leak
    drops integrity below 1.0."""
    from .identity import (
        IDENTITY_CERTAINTY_LEVELS,
    )
    ok = sum(
        1 for c in classified_claims()
        if c.certainty in (
            IDENTITY_CERTAINTY_LEVELS
        )
    )
    total = len(classified_claims())
    if total == 0:
        return 1.0
    return _round(ok / total)


__all__ = [
    "coherence_score",
    "governance_integrity",
    "identity_bias",
    "polarization_resistance",
]
