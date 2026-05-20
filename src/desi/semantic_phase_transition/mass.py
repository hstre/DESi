"""v3.52 — closed mass sweep.

The directive's named anchor counts (1, 2, 3, 4, 8)
plus the k=0 baseline and the k=20 saturation anchor.
Anchor ordering is deterministic (sort plateau ids
ascending and take the first ``k``). Probe radius is
``PROBE_RADIUS = 3.5`` — the v3.50 discrimination
band radius where per-anchor coverage spreads across
{0, 12, 121} instead of saturating at ~145.
"""
from __future__ import annotations

from ..field_leakage.census import collect_plateau_anchors


PROBE_RADIUS: float = 3.5
MASS_LEVELS: tuple[int, ...] = (0, 1, 2, 3, 4, 8)
SATURATION_MASS: int = 20


def ordered_anchor_ids() -> tuple[str, ...]:
    return tuple(sorted(
        t.trajectory_id
        for t in collect_plateau_anchors()
    ))


def first_k_ids(k: int) -> tuple[str, ...]:
    if k <= 0:
        return ()
    return ordered_anchor_ids()[:k]


def all_mass_levels() -> tuple[int, ...]:
    return MASS_LEVELS + (SATURATION_MASS,)


__all__ = [
    "MASS_LEVELS", "PROBE_RADIUS", "SATURATION_MASS",
    "all_mass_levels", "first_k_ids",
    "ordered_anchor_ids",
]
