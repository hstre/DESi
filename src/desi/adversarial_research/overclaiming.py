"""v13.2 — overclaim detection."""
from __future__ import annotations

from .manipulation import (
    ManipulationKind, fixture,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def overclaim_detection() -> float:
    """Recall on claims with confidence_claimed
    significantly above confidence_warranted.
    Threshold: gap > 0.20."""
    rows = fixture()
    target = [
        c for c in rows
        if c.confidence_claimed
        - c.confidence_warranted
        > 0.20
    ]
    if not target:
        return 1.0
    # Every overclaimer has a non-HONEST
    # ground-truth kind. We measure recall by
    # checking that detect_kind also flags
    # them (i.e., they are NOT HONEST in the
    # ground truth).
    from .selective_reporting import (
        classified_manipulations,
    )
    by_id = {
        r.claim_id: r
        for r in classified_manipulations()
    }
    detected = sum(
        1 for c in target
        if by_id[c.claim_id].detected_kind
        != ManipulationKind.HONEST.value
    )
    return _round(detected / len(target))


__all__ = [
    "overclaim_detection",
]
