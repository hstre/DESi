"""v13.1 — citation-validation summary.

Aggregates the reference + diagram checks into
a unified "citation grounding" view."""
from __future__ import annotations

from .diagram_consistency import (
    diagram_consistency, stats_consistency,
)
from .hallucinated_references import (
    citation_grounding,
    hallucinated_reference_count,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def composite_grounding() -> float:
    """Mean of citation_grounding,
    diagram_consistency, and stats_consistency.
    """
    return _round((
        citation_grounding()
        + diagram_consistency()
        + stats_consistency()
    ) / 3.0)


__all__ = [
    "composite_grounding",
]
