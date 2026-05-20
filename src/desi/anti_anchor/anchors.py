"""v3.51 — anti-anchor selection.

A closed set of strategies for choosing anti-anchor
trajectories. Anti-anchors are claims that, when added
to the active set, are required to be FAR from the
trajectory under test (Euclidean > suppression_radius).
A trajectory fires only if it is close to a plateau
anchor AND far from every anti-anchor.

* ``NONE``           — baseline (no anti-anchors)
* ``LEAKAGE_SAMPLE`` — 5 deterministic stride-samples
  from the v3.43 leakage cohort. Tests whether the
  field can be locally suppressed inside its own
  failure region.
* ``RESCUED_SAMPLE`` — 5 stride-samples from the v3.30
  rescued cohort. Tests the orthogonal arm (anti-
  anchors that are NOT near the field).
* ``PLATEAU_SAMPLE`` — 5 stride-samples from the
  plateau cohort itself. Tests the self-suppression
  extreme (anti-anchors that ARE the field).
"""
from __future__ import annotations

from enum import Enum

from ..cause_aware_control.controller import control_all
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..field_leakage.distance import trajectory_vector
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)


ANTI_RADIUS: float = 2.5
"""Suppression radius. Empirically R=2.5 with five
leakage anti-anchors zeros leakage while preserving
all 20 plateau resolutions; smaller radii leave 12
leakages and larger radii (>= 3.0) start suppressing
plateau as well."""

ANTI_COUNT: int = 5


class AntiAnchorKind(str, Enum):
    NONE             = "none"
    LEAKAGE_SAMPLE   = "leakage_sample"
    RESCUED_SAMPLE   = "rescued_sample"
    PLATEAU_SAMPLE   = "plateau_sample"


def _stride_sample(
    sorted_ids: tuple[str, ...], n: int,
) -> tuple[str, ...]:
    if not sorted_ids or n <= 0:
        return ()
    if n >= len(sorted_ids):
        return sorted_ids
    stride = max(1, len(sorted_ids) // n)
    return tuple(sorted_ids[i * stride] for i in range(n))


def select_anti_anchor_ids(
    kind: str, n: int = ANTI_COUNT,
) -> tuple[str, ...]:
    if kind == AntiAnchorKind.NONE.value:
        return ()
    if kind == AntiAnchorKind.LEAKAGE_SAMPLE.value:
        ids = sorted(
            t.trajectory_id
            for t in collect_leakage_trajectories()
        )
        return _stride_sample(tuple(ids), n)
    if kind == AntiAnchorKind.RESCUED_SAMPLE.value:
        ids = sorted(
            o.trajectory_id
            for o in control_all() if o.rescued
        )
        return _stride_sample(tuple(ids), n)
    if kind == AntiAnchorKind.PLATEAU_SAMPLE.value:
        ids = sorted(plateau_trajectory_ids())
        return _stride_sample(tuple(ids), n)
    return ()


def anti_anchor_vectors(
    kind: str, n: int = ANTI_COUNT,
) -> tuple[tuple[float, ...], ...]:
    ids = set(select_anti_anchor_ids(kind, n))
    return tuple(
        trajectory_vector(t.states)
        for t in extract_all_trajectories()
        if t.trajectory_id in ids
    )


__all__ = [
    "ANTI_COUNT", "ANTI_RADIUS", "AntiAnchorKind",
    "anti_anchor_vectors", "select_anti_anchor_ids",
]
