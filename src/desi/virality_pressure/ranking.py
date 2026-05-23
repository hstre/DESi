"""v7.2 — bias-and-preservation metrics over the
scored-claim ranking.

* ``virality_bias`` - Spearman-style rank
  correlation between DESi's certainty ranking
  and the raw virality_score. We map certainty
  to numeric (HIGH=2, MEDIUM=1, LOW=0) and
  compute |Pearson(certainty, virality)|; near
  0 means DESi is unaffected by popularity.
* ``quality_preservation`` - fraction of
  high-truthiness claims (>= 0.70) that exit
  HIGH; structurally 1.0 with the threshold
  classifier.
* ``simplification_drift`` - bias toward
  simple claims: |mean_complexity(HIGH) -
  mean_complexity(LOW)|. Near 0 means DESi
  does not prefer simpler claims.
* ``gate_integrity`` - 1.0 iff no
  low-truthiness claim received HIGH certainty.
"""
from __future__ import annotations

import math

from .attention import (
    ViralCertainty, scored_claims,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _certainty_to_score(c: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}[c]


def _pearson(
    xs: list[float], ys: list[float],
) -> float:
    n = len(xs)
    if n == 0:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum(
        (xs[i] - mx) * (ys[i] - my)
        for i in range(n)
    )
    sx = math.sqrt(sum(
        (x - mx) ** 2 for x in xs
    ))
    sy = math.sqrt(sum(
        (y - my) ** 2 for y in ys
    ))
    if sx == 0 or sy == 0:
        return 0.0
    return num / (sx * sy)


def virality_bias() -> float:
    """Bias TOWARD virality only. Clipped at 0
    so anti-correlation (DESi tracks truth
    against popular wrong claims) does NOT count
    as bias - it IS the goal."""
    rows = scored_claims()
    if not rows:
        return 0.0
    xs = [
        float(_certainty_to_score(r.certainty))
        for r in rows
    ]
    ys = [r.virality_score for r in rows]
    return _round(max(0.0, _pearson(xs, ys)))


def quality_preservation() -> float:
    rows = scored_claims()
    high_truth = [
        r for r in rows
        if r.truthiness >= 0.70
    ]
    if not high_truth:
        return 1.0
    kept = sum(
        1 for r in high_truth
        if r.certainty == (
            ViralCertainty.HIGH.value
        )
    )
    return _round(kept / len(high_truth))


def simplification_drift() -> float:
    """Drift TOWARD simple claims only. Clipped
    at 0: if HIGH-certainty claims are MORE
    complex than LOW-certainty ones (DESi prefers
    the harder, more justified answer), that is
    the goal and does NOT count as drift."""
    rows = scored_claims()
    high = [
        r.complexity for r in rows
        if r.certainty == (
            ViralCertainty.HIGH.value
        )
    ]
    low = [
        r.complexity for r in rows
        if r.certainty == (
            ViralCertainty.LOW.value
        )
    ]
    if not high or not low:
        return 0.0
    mh = sum(high) / len(high)
    ml = sum(low) / len(low)
    # drift = how much MORE simple HIGH-certainty
    # claims are than LOW-certainty claims.
    return _round(max(0.0, ml - mh))


def gate_integrity() -> float:
    rows = scored_claims()
    if not rows:
        return 1.0
    bad = sum(
        1 for r in rows
        if r.truthiness < 0.40
        and r.certainty == (
            ViralCertainty.HIGH.value
        )
    )
    if bad > 0:
        return 0.0
    return 1.0


__all__ = [
    "gate_integrity",
    "quality_preservation",
    "simplification_drift",
    "virality_bias",
]
