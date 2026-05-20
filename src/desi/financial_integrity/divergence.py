"""v14 — cashflow-vs-profit divergence,
receivables growth, and margin-stability
signals.

All functions read ONLY the published financial
fields. None of them read ``post_hoc_label`` -
the post-hoc legal outcome must never feed the
ex-ante scoring."""
from __future__ import annotations

from .statements import statements


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def cashflow_profit_divergence() -> float:
    """Mean (reported_net_profit -
    operating_cash_flow) / reported_net_profit
    across all years. High = reported profit not
    backed by cash. A classic audit-worthy
    signal - NOT a fraud conclusion."""
    rows = statements()
    if not rows:
        return 0.0
    gaps = []
    for s in rows:
        if s.reported_net_profit_eur_m > 0:
            gaps.append(
                (
                    s.reported_net_profit_eur_m
                    - s.operating_cash_flow_eur_m
                )
                / s.reported_net_profit_eur_m,
            )
    if not gaps:
        return 0.0
    return _round(sum(gaps) / len(gaps))


def receivables_growth() -> float:
    """Compound annual growth of receivables
    MINUS compound annual growth of revenue
    across the window. Positive means
    receivables outpace revenue (audit-worthy
    working-capital signal)."""
    rows = sorted(
        statements(),
        key=lambda s: s.fiscal_year,
    )
    if len(rows) < 2:
        return 0.0
    first, last = rows[0], rows[-1]
    n = last.fiscal_year - first.fiscal_year
    if n <= 0:
        return 0.0

    def _cagr(a: float, b: float) -> float:
        if a <= 0 or b <= 0:
            return 0.0
        return (b / a) ** (1.0 / n) - 1.0

    rec = _cagr(
        first.receivables_eur_m,
        last.receivables_eur_m,
    )
    rev = _cagr(
        first.reported_revenue_eur_m,
        last.reported_revenue_eur_m,
    )
    return _round(rec - rev)


def unexplained_margin_stability() -> float:
    """Suspiciously stable margins under rapid
    growth are audit-worthy. We score:
    1 - (margin standard deviation scaled). A
    value near 1.0 means margins barely move
    despite the revenue more than doubling -
    which warrants a closer look at how the
    margin is held so constant."""
    rows = statements()
    margins = [s.net_margin for s in rows]
    if len(margins) < 2:
        return 0.0
    mean = sum(margins) / len(margins)
    var = sum(
        (m - mean) ** 2 for m in margins
    ) / len(margins)
    std = var ** 0.5
    # Scale: a std of 0.05 maps to stability 0.5;
    # std of 0 maps to stability 1.0.
    stability = max(0.0, 1.0 - std / 0.05)
    return _round(stability)


__all__ = [
    "cashflow_profit_divergence",
    "receivables_growth",
    "unexplained_margin_stability",
]
