"""v14 — third-party-acquirer dependency,
audit-trail opacity, and geographic-revenue
opacity signals.

Reads only published fields - never the
post-hoc label."""
from __future__ import annotations

from .statements import statements


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def third_party_acquirer_dependency() -> float:
    """Mean TPA-revenue / total-revenue across
    years. High dependency on third-party
    acquiring partners (hard to independently
    verify) is audit-worthy."""
    rows = statements()
    shares = []
    for s in rows:
        if s.reported_revenue_eur_m > 0:
            shares.append(
                s.tpa_revenue_eur_m
                / s.reported_revenue_eur_m,
            )
    if not shares:
        return 0.0
    return _round(sum(shares) / len(shares))


def audit_trail_opacity() -> float:
    """Mean escrow-balance / reported-net-profit
    across years. Escrow / trust balances that
    dwarf the profit they supposedly secure are
    audit-worthy: the audit trail to confirm
    they exist is the crux. Normalised to [0,1]
    by capping the ratio at 5x."""
    rows = statements()
    ratios = []
    for s in rows:
        if s.reported_net_profit_eur_m > 0:
            r = (
                s.escrow_balance_eur_m
                / s.reported_net_profit_eur_m
            )
            ratios.append(min(r, 5.0) / 5.0)
    if not ratios:
        return 0.0
    return _round(sum(ratios) / len(ratios))


def geographic_revenue_opacity() -> float:
    """Mean APAC-revenue / total-revenue.
    Concentration in hard-to-audit regions is
    audit-worthy (it is the verifiability that
    matters, not the geography itself)."""
    rows = statements()
    shares = []
    for s in rows:
        if s.reported_revenue_eur_m > 0:
            shares.append(
                s.apac_revenue_eur_m
                / s.reported_revenue_eur_m,
            )
    if not shares:
        return 0.0
    return _round(sum(shares) / len(shares))


__all__ = [
    "audit_trail_opacity",
    "geographic_revenue_opacity",
    "third_party_acquirer_dependency",
]
