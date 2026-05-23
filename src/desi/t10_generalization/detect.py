"""v3.105 — per-entanglement information loss
estimate.

For each entanglement type we estimate latent
information loss by reusing the v3.100 upper-
bound model: in the degenerate representation
all member families collapse to a single
downstream point, so the loss is
``1 - (1 / family_count)`` of the family-aware
diversity the collapse hides.
"""
from __future__ import annotations

from .census import (
    EntanglementType,
    all_entanglement_instances,
    all_entanglement_types,
    candidate_families,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def family_count_in_entanglements() -> int:
    """Distinct families involved in any
    entanglement type with >= 2 members."""
    seen: set[str] = set()
    for t in all_entanglement_types():
        if len(t.families) >= 2:
            seen.update(t.families)
    return len(seen)


def entanglement_type_information_loss(
    et: EntanglementType,
) -> float:
    """Same upper bound as v3.100:
    1 - 1 / family_count."""
    n = len(et.families)
    if n <= 1:
        return 0.0
    return _round(1.0 - 1.0 / n)


def mean_information_loss() -> float:
    types = [
        t for t in all_entanglement_types()
        if len(t.families) >= 2
    ]
    if not types:
        return 0.0
    losses = [
        entanglement_type_information_loss(t)
        for t in types
    ]
    return _round(sum(losses) / len(losses))


def hidden_entanglement_count() -> int:
    """Cross-family pair count - the EXPLICIT
    instance set passing both filters
    (text_overlap < 0.10, centroid collapse).
    May undercount the theoretical maximum
    ``C(family_count, 2)`` when intra-cluster
    pairs share too much vocabulary to count as
    semantic doppelgangers."""
    return len(all_entanglement_instances())


def entanglement_type_count() -> int:
    return sum(
        1 for t in all_entanglement_types()
        if len(t.families) >= 2
    )


__all__ = [
    "entanglement_type_count",
    "entanglement_type_information_loss",
    "family_count_in_entanglements",
    "hidden_entanglement_count",
    "mean_information_loss",
]
