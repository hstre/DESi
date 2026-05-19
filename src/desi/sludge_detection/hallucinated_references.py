"""v13.1 — hallucinated-reference detection."""
from __future__ import annotations

from ..paper_integrity.claims import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def citation_grounding() -> float:
    """Citation grounding measured on papers
    that DESi ACCEPTS (verdict != SLUDGE).

    Sludge papers are filtered out before the
    metric is computed - the concept gate is
    about whether legitimate papers have
    grounded citations, not about whether
    sludge survives the audit. Sludge survival
    is captured separately by
    ``fake_paper_recall``.
    """
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
    accepted = [
        c for c in fixture()
        if c.paper_id in accepted_ids
    ]
    if not accepted:
        return 0.0
    ok = sum(
        1 for c in accepted
        if c.references_grounded
    )
    return _round(ok / len(accepted))


def hallucinated_reference_count() -> int:
    return sum(
        1 for c in fixture()
        if not c.references_grounded
    )


__all__ = [
    "citation_grounding",
    "hallucinated_reference_count",
]
