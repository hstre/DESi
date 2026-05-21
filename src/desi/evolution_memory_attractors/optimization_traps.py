"""v30.2 - optimization traps.

An optimisation trap is an area where evolution keeps proposing
but never makes progress - here, an area whose every mutation was
rejected (a stagnant local maximum). These are surfaced so the
trap is visible, not so it is auto-avoided.
"""
from __future__ import annotations

from desi.evolution_memory import mutations

from .mutation_clusters import clusters_by_area


def _area_outcomes() -> dict[str, tuple[int, int]]:
    """area -> (accepted_count, rejected_count)."""
    acc: dict[str, int] = {}
    rej: dict[str, int] = {}
    for m in mutations():
        if m.accepted:
            acc[m.target_area] = acc.get(m.target_area, 0) + 1
        else:
            rej[m.target_area] = rej.get(m.target_area, 0) + 1
    areas = set(acc) | set(rej)
    return {
        a: (acc.get(a, 0), rej.get(a, 0)) for a in areas
    }


def optimization_traps() -> tuple[str, ...]:
    """Areas where every mutation was rejected (stagnant)."""
    out = []
    for area, (a, r) in _area_outcomes().items():
        if r >= 1 and a == 0:
            out.append(area)
    return tuple(sorted(out))


def productive_areas() -> tuple[str, ...]:
    """Areas with at least one accepted mutation."""
    return tuple(sorted(
        a for a, (acc, _) in _area_outcomes().items() if acc >= 1
    ))


def trap_visibility() -> float:
    """Fraction of all-rejected areas surfaced as traps, in
    [0, 1]."""
    all_rejected = [
        a for a, (acc, r) in _area_outcomes().items()
        if r >= 1 and acc == 0
    ]
    if not all_rejected:
        return 1.0
    surfaced = set(optimization_traps())
    return round(
        sum(1 for a in all_rejected if a in surfaced)
        / len(all_rejected), 6,
    )


__all__ = [
    "optimization_traps",
    "productive_areas",
    "trap_visibility",
]
