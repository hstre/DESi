"""v3.47 — tail-aligned trajectory geometry.

The plateau cohort (5 states), the leakage cohort (5
states) and the rescued cohort (5 states) have a fixed
trajectory length; the GAP cases are 8 states long.
To compare them on a common feature space, we use the
``tail_vector``: the last ``TAIL_LENGTH`` (= 5) states
concatenated into a 45-d vector. For length-5
trajectories this is the full trajectory_vector;
for the 8-state GAP cases it is states 3..7.

Pure-Python; reuses v3.38's Euclidean primitive via
v3.43's manifold_distance helper.
"""
from __future__ import annotations

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from ..field_leakage.distance import (
    euclidean, manifold_distance,
)


TAIL_LENGTH: int = 5


def tail_vector(
    states: tuple[StateVector, ...],
) -> tuple[float, ...]:
    """Concatenate the last ``TAIL_LENGTH`` state
    vectors into a 45-d feature vector. Trajectories
    shorter than ``TAIL_LENGTH`` are left-padded with
    zeros (no such case in the current corpus; the
    pad is a defensive default)."""
    tail = states[-TAIL_LENGTH:]
    pad = TAIL_LENGTH - len(tail)
    out: list[float] = []
    for _ in range(pad):
        out.extend([0.0] * len(DIMENSION_NAMES))
    for s in tail:
        out.extend(s.to_tuple())
    return tuple(out)


def final_state_vector(
    states: tuple[StateVector, ...],
) -> tuple[float, ...]:
    return states[-1].to_tuple()


__all__ = [
    "TAIL_LENGTH", "euclidean", "final_state_vector",
    "manifold_distance", "tail_vector",
]
