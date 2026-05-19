"""v8.0 — tradeoff metrics over the schedule."""
from __future__ import annotations

import math

from .budget import (
    ScheduleDecision, schedule,
)


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


def resource_bias() -> float:
    """Bias TOWARD cheap claims, clipped at 0.
    Correlation between PROCESS-status and
    (negative complexity_cost). Positive => the
    scheduler favours cheap over expensive
    REGARDLESS of value. Zero means the choice
    tracks value, not cost."""
    rows = schedule()
    if not rows:
        return 0.0
    is_process = [
        1.0 if r.decision == (
            ScheduleDecision.PROCESS.value
        ) else 0.0
        for r in rows
    ]
    neg_cost = [
        -r.complexity_cost for r in rows
    ]
    return _round(
        max(0.0, _pearson(is_process, neg_cost)),
    )


def complexity_preservation() -> float:
    """Fraction of HIGH-value (>= 0.70) claims
    that survived the budget without being
    SKIPPED. PROCESS and DEFER both count as
    preserved - the directive's invariant is
    that valuable complex claims are NOT
    silently dropped, NOT that they all get
    processed immediately."""
    rows = schedule()
    high = [
        r for r in rows
        if r.epistemic_value >= 0.70
    ]
    if not high:
        return 1.0
    preserved = sum(
        1 for r in high
        if r.decision != (
            ScheduleDecision.SKIP.value
        )
    )
    return _round(preserved / len(high))


def cheap_solution_drift() -> float:
    """Mean complexity of PROCESSED claims
    minus mean complexity of the corpus,
    NEGATIVE clipped to 0. If processed claims
    are systematically simpler than the corpus,
    this is positive."""
    rows = schedule()
    proc = [
        r.complexity_cost for r in rows
        if r.decision == (
            ScheduleDecision.PROCESS.value
        )
    ]
    if not proc or not rows:
        return 0.0
    mp = sum(proc) / len(proc)
    mc = sum(r.complexity_cost for r in rows) / (
        len(rows)
    )
    return _round(max(0.0, mc - mp))


def governance_integrity() -> float:
    """Every scheduled row MUST emit a closed
    Decision value. Leakage drops this below 1.
    """
    rows = schedule()
    if not rows:
        return 1.0
    ok = sum(
        1 for r in rows
        if r.decision in (
            d.value for d in ScheduleDecision
        )
    )
    return _round(ok / len(rows))


__all__ = [
    "cheap_solution_drift",
    "complexity_preservation",
    "governance_integrity",
    "resource_bias",
]
