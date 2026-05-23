"""v13.1 — diagram & statistics consistency."""
from __future__ import annotations

from ..paper_integrity.claims import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _accepted_papers():
    """Papers DESi did NOT flag as SLUDGE."""
    from .sludge import (
        SludgeVerdict, classified_papers,
    )
    accepted_ids = {
        p.paper_id
        for p in classified_papers()
        if p.verdict != (
            SludgeVerdict.SLUDGE.value
        )
    }
    return [
        c for c in fixture()
        if c.paper_id in accepted_ids
    ]


def diagram_consistency() -> float:
    """Diagram consistency on ACCEPTED papers
    only. Sludge is filtered (its hallucinated-
    diagram rate is captured in
    fake_paper_recall)."""
    accepted = _accepted_papers()
    if not accepted:
        return 0.0
    ok = sum(
        1 for c in accepted
        if not c.has_hallucinated_diagram
    )
    return _round(ok / len(accepted))


def stats_consistency() -> float:
    """Stats consistency on ACCEPTED papers."""
    accepted = _accepted_papers()
    if not accepted:
        return 0.0
    ok = sum(
        1 for c in accepted
        if not c.has_hallucinated_stats
    )
    return _round(ok / len(accepted))


__all__ = [
    "diagram_consistency",
    "stats_consistency",
]
