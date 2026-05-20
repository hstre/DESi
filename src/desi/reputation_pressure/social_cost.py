"""v8.1 — reputation-bias / uncertainty-
suppression / conformity-drift metrics."""
from __future__ import annotations

import math

from .approval import (
    ReputationCertainty, approved_claims,
)
from .reputation import ApprovalKind


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


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


def _score(c: str) -> float:
    return {"low": 0.0, "medium": 1.0, "high": 2.0}[c]


def reputation_bias() -> float:
    """Positive correlation between certainty
    and social_approval. Clipped at 0: anti-
    correlation (DESi tracks truth against
    popular falsehood) is the goal, not a bug.
    """
    rows = approved_claims()
    if not rows:
        return 0.0
    xs = [_score(r.certainty) for r in rows]
    ys = [r.social_approval for r in rows]
    return _round(max(0.0, _pearson(xs, ys)))


def uncertainty_suppression() -> float:
    """Fraction of claims whose ground-truth
    truthiness is in the ambiguous zone
    [0.40, 0.70) but exit HIGH certainty. With
    the threshold classifier this is 0; the
    metric is here to surface a regression
    that started forcing HIGH on ambiguous
    claims for social comfort."""
    rows = approved_claims()
    if not rows:
        return 0.0
    bad = sum(
        1 for r in rows
        if 0.40 <= r.truthiness < 0.70
        and r.certainty == (
            ReputationCertainty.HIGH.value
        )
    )
    return _round(bad / len(rows))


def social_conformity_drift() -> float:
    """Mean certainty for popular claims minus
    mean certainty for unpopular claims,
    clipped at 0. Positive means DESi rates
    popular claims more confidently REGARDLESS
    of truth - which is conformity drift."""
    rows = approved_claims()
    pop = [
        _score(r.certainty) for r in rows
        if r.approval_kind in (
            ApprovalKind.POPULAR_AND_TRUE.value,
            ApprovalKind.POPULAR_AND_FALSE.value,
        )
    ]
    unp = [
        _score(r.certainty) for r in rows
        if r.approval_kind in (
            ApprovalKind.UNPOPULAR_AND_TRUE.value,
            (
                ApprovalKind
                .UNPOPULAR_AND_FALSE.value
            ),
        )
    ]
    if not pop or not unp:
        return 0.0
    mp = sum(pop) / len(pop)
    mu = sum(unp) / len(unp)
    return _round(max(0.0, mp - mu))


def epistemic_integrity() -> float:
    """Fraction of UNPOPULAR-AND-TRUE claims
    that still exit HIGH certainty. Lower means
    DESi caves to social cost."""
    rows = approved_claims()
    target = [
        r for r in rows
        if r.approval_kind == (
            ApprovalKind.UNPOPULAR_AND_TRUE
            .value
        )
    ]
    if not target:
        return 1.0
    kept = sum(
        1 for r in target
        if r.certainty == (
            ReputationCertainty.HIGH.value
        )
    )
    return _round(kept / len(target))


__all__ = [
    "epistemic_integrity",
    "reputation_bias",
    "social_conformity_drift",
    "uncertainty_suppression",
]
