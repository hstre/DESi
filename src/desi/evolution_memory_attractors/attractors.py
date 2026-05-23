"""v30.2 - evolutionary attractors.

An attractor is a target area that repeatedly attracts mutation
ideas (a recurring mutation type / convergence point). Surfaced
descriptively; an attractor is not a recommendation.
"""
from __future__ import annotations

from .mutation_clusters import clusters_by_area


def attractors() -> dict[str, tuple[str, ...]]:
    """Target areas that attract at least two mutation ideas."""
    return {
        area: ms
        for area, ms in clusters_by_area().items()
        if len(ms) >= 2
    }


def attractor_areas() -> tuple[str, ...]:
    return tuple(sorted(attractors()))


def attractor_visibility() -> float:
    """Fraction of areas that attract >=2 mutations and are
    surfaced as attractors, in [0, 1]."""
    eligible = [
        area for area, ms in clusters_by_area().items()
        if len(ms) >= 2
    ]
    if not eligible:
        return 1.0
    surfaced = set(attractor_areas())
    seen = sum(1 for a in eligible if a in surfaced)
    return round(seen / len(eligible), 6)


def evolution_diversity() -> float:
    """1 - (largest cluster share). High means evolution is not
    collapsing into a single attractor, in [0, 1]."""
    clusters = clusters_by_area()
    total = sum(len(ms) for ms in clusters.values())
    if total == 0:
        return 0.0
    largest = max(len(ms) for ms in clusters.values())
    return round(1.0 - largest / total, 6)


__all__ = [
    "attractor_areas",
    "attractor_visibility",
    "attractors",
    "evolution_diversity",
]
