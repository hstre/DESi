"""v3.44 — radius-bounded selector.

A "policy radius" gates Strategy B by geometric
distance to the plateau manifold instead of by a
single pre-audit feature value. The selector fires on
a trajectory iff its 45-d trajectory vector is within
Euclidean distance ``r`` of at least one plateau
anchor.

Closed radius set (directive § v3.44):

    0.25, 0.5, 1.0, 2.0, 4.0, ∞

Reuses ``manifold_distance`` from v3.43.
"""
from __future__ import annotations

from math import inf

from ..epistemic_trajectory.state import StateVector
from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)


RADII: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0, inf)


def selector_for_radius(
    states: tuple[StateVector, ...], radius: float,
    plateau_vecs: tuple[tuple[float, ...], ...],
) -> bool:
    if radius < 0:
        return False
    vec = trajectory_vector(states)
    d, _ = manifold_distance(vec, plateau_vecs)
    return d <= radius


def radius_label(radius: float) -> str:
    if radius == inf:
        return "inf"
    return f"{radius:g}"


__all__ = [
    "RADII", "radius_label", "selector_for_radius",
]
