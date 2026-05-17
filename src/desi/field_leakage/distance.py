"""v3.43 — distance utilities for the field-leakage
audit.

Reuses v3.38's pure-Python Euclidean helpers and adds
``manifold_distance``: the minimum distance from a
single trajectory vector to a set of anchor vectors
(the "plateau manifold" being the 20 plateau
trajectories).
"""
from __future__ import annotations

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from ..plateau_separation.distance import (
    euclidean, trajectory_vector,
)


def manifold_distance(
    point: tuple[float, ...],
    manifold: tuple[tuple[float, ...], ...],
) -> tuple[float, int]:
    """Minimum Euclidean distance from ``point`` to any
    vector in ``manifold``. Returns ``(distance,
    nearest_index)``. ``nearest_index = -1`` when
    ``manifold`` is empty."""
    if not manifold:
        return float("inf"), -1
    best_d = float("inf")
    best_i = -1
    for i, m in enumerate(manifold):
        d = euclidean(point, m)
        if d < best_d:
            best_d = d
            best_i = i
    return best_d, best_i


def per_state_dim_overlap(
    a: tuple[StateVector, ...],
    b: tuple[StateVector, ...], dim: str, index: int,
) -> bool:
    """True when ``a[index].<dim> == b[index].<dim>``.
    Used to read off "same frame family", "same support
    family" style booleans."""
    if index >= min(len(a), len(b)):
        return False
    return getattr(a[index], dim) == getattr(b[index], dim)


__all__ = [
    "DIMENSION_NAMES", "euclidean", "manifold_distance",
    "per_state_dim_overlap", "trajectory_vector",
]
