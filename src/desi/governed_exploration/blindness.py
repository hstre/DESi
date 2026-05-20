"""v12.1 — exploration-blindness detection.

A BLINDNESS POOL emerges when the wild brother
emits NO hypothesis of a given (shape, status)
combination that the audit pipeline could in
principle accept. We measure the share of
closed-enum shape x status cells that received
no hypothesis at all - these are blind spots."""
from __future__ import annotations

from ..open_math.explorer import (
    HYPOTHESIS_SHAPES,
)
from ..open_math.governance import (
    governed_hypotheses,
)
from ..open_math.hypotheses import (
    EPISTEMIC_STATUSES,
)


def covered_cells() -> set[tuple[str, str]]:
    """Set of (shape, status) cells that have
    at least one hypothesis in them."""
    return {
        (g.shape, g.detected_status)
        for g in governed_hypotheses()
    }


def total_cells() -> int:
    return (
        len(HYPOTHESIS_SHAPES)
        * len(EPISTEMIC_STATUSES)
    )


def blindness_share() -> float:
    """Fraction of cells with zero hypotheses.
    A high share means broad audit-surface
    blindness; we report it for transparency
    but the actual gate is at v12.4."""
    covered = len(covered_cells())
    total = total_cells()
    if total == 0:
        return 0.0
    return round(
        (total - covered) / total, 6,
    )


def covered_share() -> float:
    return round(1.0 - blindness_share(), 6)


__all__ = [
    "blindness_share",
    "covered_cells",
    "covered_share",
    "total_cells",
]
