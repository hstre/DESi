"""v13.2 — confidence-inflation and
methodological-integrity metrics."""
from __future__ import annotations

from .manipulation import (
    ManipulationKind, fixture,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def false_certainty_rate() -> float:
    """Fraction of fixture claims whose
    confidence_claimed is HIGH (>= 0.80) but
    confidence_warranted is LOW (< 0.50). DESi
    should cap such claims at v13.4. The metric
    is here to surface the ground-truth scale
    of the manipulation pressure."""
    rows = fixture()
    if not rows:
        return 0.0
    inflated = sum(
        1 for c in rows
        if c.confidence_claimed >= 0.80
        and c.confidence_warranted < 0.50
    )
    return _round(inflated / len(rows))


def methodological_integrity() -> float:
    """Fraction of claims tagged HONEST in the
    ground truth. Composite with the
    methodological-laundering subset: every
    HONEST claim must NOT be in the laundering
    set."""
    rows = fixture()
    if not rows:
        return 0.0
    honest = sum(
        1 for c in rows
        if c.kind == (
            ManipulationKind.HONEST.value
        )
    )
    return _round(honest / len(rows))


def detection_recall_on_inflated() -> float:
    """Of the false-certainty claims, what
    fraction does the detector identify as
    non-HONEST?"""
    from .selective_reporting import (
        classified_manipulations,
    )
    rows = fixture()
    inflated = [
        c for c in rows
        if c.confidence_claimed >= 0.80
        and c.confidence_warranted < 0.50
    ]
    if not inflated:
        return 1.0
    by_id = {
        r.claim_id: r
        for r in classified_manipulations()
    }
    detected = sum(
        1 for c in inflated
        if by_id[c.claim_id].detected_kind
        != ManipulationKind.HONEST.value
    )
    return _round(detected / len(inflated))


__all__ = [
    "detection_recall_on_inflated",
    "false_certainty_rate",
    "methodological_integrity",
]
