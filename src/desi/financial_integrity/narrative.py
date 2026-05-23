"""v14 — narrative-vs-numbers mismatch and
bridge-required-disclosure signals.

Reads only published fields - never the
post-hoc label."""
from __future__ import annotations

from .statements import statements


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def narrative_numbers_mismatch() -> float:
    """Mean gap between management narrative
    optimism and the cash-backing of reported
    profit. For each year:

      mismatch = narrative_optimism
                 - (operating_cash_flow /
                    reported_net_profit)

    A high mismatch means the story is far
    rosier than the cash conversion - an
    audit-worthy narrative-vs-numbers gap.
    Clipped at 0."""
    rows = statements()
    gaps = []
    for s in rows:
        if s.reported_net_profit_eur_m > 0:
            cash_backing = (
                s.operating_cash_flow_eur_m
                / s.reported_net_profit_eur_m
            )
            gaps.append(max(
                0.0,
                s.narrative_optimism
                - cash_backing,
            ))
    if not gaps:
        return 0.0
    return _round(sum(gaps) / len(gaps))


def bridge_required_disclosures() -> float:
    """Fraction of REQUIRED disclosure bridges
    that were NOT provided, averaged across
    years. High = many claims rest on
    disclosures that are demanded but missing -
    audit-worthy."""
    rows = statements()
    fracs = []
    for s in rows:
        req = s.disclosure_bridges_required
        prov = s.disclosure_bridges_provided
        if req > 0:
            missing = max(0, req - prov)
            fracs.append(missing / req)
    if not fracs:
        return 0.0
    return _round(sum(fracs) / len(fracs))


__all__ = [
    "bridge_required_disclosures",
    "narrative_numbers_mismatch",
]
