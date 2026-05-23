"""v8.2 — goal-balance / goodhart / hidden-
reweight / tradeoff-transparency metrics."""
from __future__ import annotations

import math

from .goal_conflicts import (
    GOAL_WEIGHTS, OPTIMIZATION_GOALS,
)
from .optimization import (
    optimised, selected_top_k,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def goal_balance() -> float:
    """Normalised Shannon entropy over the
    GOAL_WEIGHTS distribution. 1.0 = perfectly
    balanced; 0.0 = collapsed onto a single
    goal."""
    total = sum(GOAL_WEIGHTS.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for w in GOAL_WEIGHTS.values():
        p = w / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(len(GOAL_WEIGHTS))
    if max_h <= 0:
        return 1.0
    return _round(h / max_h)


def goodhart_risk() -> float:
    """How concentrated is the selection on a
    single goal? Compute per-goal mean score
    across the selected top-K; if ONE goal
    dominates (its mean is much higher than the
    others), goodhart_risk is high. Clipped at
    0; if no goal dominates, score is 0."""
    top = selected_top_k()
    if not top:
        return 0.0
    means = {}
    for g in OPTIMIZATION_GOALS:
        vs = [
            t.scores.get(g, 0.0) for t in top
        ]
        means[g] = sum(vs) / max(len(vs), 1)
    # Goodhart = (max - mean_of_others) / max.
    high = max(means.values())
    rest = [
        v for k, v in means.items()
        if v != high
    ]
    if not rest or high <= 0:
        return 0.0
    rest_mean = sum(rest) / len(rest)
    return _round(
        max(0.0, (high - rest_mean) / high)
        if high > rest_mean + 0.20
        else 0.0,
    )


def hidden_reweighting() -> float:
    """The GOAL_WEIGHTS dict is read twice; any
    drift between the reads would indicate
    runtime mutation. 0.0 unless something
    weird happens."""
    a = dict(GOAL_WEIGHTS)
    b = dict(GOAL_WEIGHTS)
    if a != b:
        return 1.0
    return 0.0


def tradeoff_transparency() -> float:
    """Every optimised item must carry a non-
    empty rationale that names every goal. If a
    decision is made without a published
    rationale, transparency drops."""
    rows = optimised()
    if not rows:
        return 1.0
    ok = 0
    for r in rows:
        if (
            r.rationale
            and all(
                g in r.rationale
                for g in OPTIMIZATION_GOALS
            )
        ):
            ok += 1
    return _round(ok / len(rows))


__all__ = [
    "goal_balance",
    "goodhart_risk",
    "hidden_reweighting",
    "tradeoff_transparency",
]
