"""v15.0 — narrative-consistency structure
signal.

Does the management narrative tone stay within
reach of what the numbers (cash backing of
reported profit) support? A story that runs far
ahead of the cash conversion is an audit-worthy
narrative-vs-numbers gap - NOT a fraud claim.

Reads ONLY published fields. Never the post-hoc
label.
"""
from __future__ import annotations

from .statements import Firm, firms


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def narrative_consistency_firm(firm: Firm) -> float:
    """Mean of (1 - narrative_vs_numbers_gap)
    across the firm's profitable years, in [0, 1].
    High = the story matches the cash conversion;
    low = optimism outruns the cash backing."""
    scores: list[float] = []
    for y in firm.years:
        if y.reported_net_profit_eur_m <= 0:
            continue
        cash_backing = _clip01(
            y.operating_cash_flow_eur_m
            / y.reported_net_profit_eur_m,
        )
        gap = max(
            0.0,
            y.narrative_optimism - cash_backing,
        )
        scores.append(_clip01(1.0 - gap))
    if not scores:
        return 0.0
    return _round(sum(scores) / len(scores))


def narrative_consistency() -> float:
    """Corpus mean of per-firm narrative
    consistency."""
    rows = firms()
    if not rows:
        return 0.0
    vals = [
        narrative_consistency_firm(f)
        for f in rows
    ]
    return _round(sum(vals) / len(vals))


__all__ = [
    "narrative_consistency",
    "narrative_consistency_firm",
]
