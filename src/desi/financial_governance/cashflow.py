"""v15.0 — cashflow-alignment structure signal.

How well does reported operating cash flow back
reported net profit? Low alignment is an audit-
worthy structural tension - NOT a fraud claim.

Reads ONLY published fields. Never the post-hoc
label.
"""
from __future__ import annotations

from .statements import Firm, firms


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def firm_cash_backing(firm: Firm) -> list[float]:
    """Per-year min(operating_cash_flow /
    net_profit, 1.0) for profitable years."""
    out: list[float] = []
    for y in firm.years:
        if y.reported_net_profit_eur_m > 0:
            out.append(_clip01(
                y.operating_cash_flow_eur_m
                / y.reported_net_profit_eur_m,
            ))
    return out


def cashflow_alignment_firm(firm: Firm) -> float:
    """Mean cash-backing across the firm's years,
    in [0, 1]. 1.0 = profit fully backed by cash;
    low = reported profit runs ahead of cash."""
    backing = firm_cash_backing(firm)
    if not backing:
        return 0.0
    return _round(sum(backing) / len(backing))


def cashflow_alignment() -> float:
    """Corpus mean of per-firm cashflow
    alignment."""
    rows = firms()
    if not rows:
        return 0.0
    vals = [
        cashflow_alignment_firm(f) for f in rows
    ]
    return _round(sum(vals) / len(vals))


__all__ = [
    "cashflow_alignment",
    "cashflow_alignment_firm",
    "firm_cash_backing",
]
