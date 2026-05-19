"""v15.0 — disclosure-integrity structure
signals: bridge validity and opacity detection.

* bridge_validity: fraction of REQUIRED
  disclosure bridges that were actually provided.
  Low = many claims rest on disclosures that are
  demanded but missing.
* opacity_detection: how much of the structure is
  hard to see through - goodwill / intangibles
  relative to revenue, plus the share of revenue
  not broken out by segment. High = more opacity
  for a human auditor to push on.

Both are audit-worthiness signals, NOT fraud
claims. They read ONLY published fields, never
the post-hoc label.
"""
from __future__ import annotations

from .statements import Firm, firms

# A goodwill/revenue ratio at or above this maps
# the goodwill opacity component to 1.0.
_GOODWILL_CAP = 0.5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def bridge_validity_firm(firm: Firm) -> float:
    """Mean provided/required disclosure-bridge
    ratio across the firm's years, in [0, 1].
    1.0 = every required bridge provided."""
    fracs: list[float] = []
    for y in firm.years:
        req = y.disclosure_bridges_required
        prov = y.disclosure_bridges_provided
        if req > 0:
            fracs.append(_clip01(prov / req))
    if not fracs:
        return 0.0
    return _round(sum(fracs) / len(fracs))


def opacity_firm(firm: Firm) -> float:
    """Mean per-year opacity in [0, 1]: half from
    goodwill/intangibles vs revenue (capped), half
    from the undisclosed-segment revenue share."""
    scores: list[float] = []
    for y in firm.years:
        rev = y.reported_revenue_eur_m
        goodwill_comp = _clip01(
            (y.goodwill_intangibles_eur_m / rev)
            / _GOODWILL_CAP,
        ) if rev > 0 else 0.0
        seg_comp = _clip01(
            y.undisclosed_segment_share,
        )
        scores.append(_clip01(
            0.5 * goodwill_comp + 0.5 * seg_comp,
        ))
    if not scores:
        return 0.0
    return _round(sum(scores) / len(scores))


def bridge_validity() -> float:
    """Corpus mean of per-firm bridge validity."""
    rows = firms()
    if not rows:
        return 0.0
    vals = [bridge_validity_firm(f) for f in rows]
    return _round(sum(vals) / len(vals))


def opacity_detection() -> float:
    """Corpus mean of per-firm opacity."""
    rows = firms()
    if not rows:
        return 0.0
    vals = [opacity_firm(f) for f in rows]
    return _round(sum(vals) / len(vals))


__all__ = [
    "bridge_validity",
    "bridge_validity_firm",
    "opacity_detection",
    "opacity_firm",
]
