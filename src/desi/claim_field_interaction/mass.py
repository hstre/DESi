"""v3.45 — claim-mass activation.

Vary the number of activated plateau anchors used by
the v3.44 radius-bounded selector. The closed mass
set (directive § v3.45) is:

    0, 1, 2, 4, 8

plus the full plateau mass (20) as the saturation
reference.

Anchor ordering is deterministic: sort plateau
trajectories by ``trajectory_id`` (alphabetical) and
take the first ``k``. ``k = 0`` corresponds to "no
anchors active" → the policy never fires.

The probe radius is fixed at ``PROBE_RADIUS = 4.0`` -
the smallest radius from v3.44's closed RADII set that
exposes the leakage cohort (v3.44's curve transitions
from 0 to 145 leakage between r=2.0 and r=4.0). At
this radius the per-anchor leakage contribution is
observable.
"""
from __future__ import annotations

from typing import Sequence

from ..epistemic_trajectory.extractor import Trajectory
from ..field_leakage.census import collect_plateau_anchors
from ..field_leakage.distance import trajectory_vector


PROBE_RADIUS: float = 4.0
MASS_LEVELS: tuple[int, ...] = (0, 1, 2, 4, 8)
SATURATION_MASS: int = 20


def ordered_plateau_anchors() -> tuple[Trajectory, ...]:
    """Plateau trajectories sorted by trajectory_id for
    deterministic mass-activation order."""
    anchors = list(collect_plateau_anchors())
    anchors.sort(key=lambda t: t.trajectory_id)
    return tuple(anchors)


def active_anchor_subset(
    k: int,
) -> tuple[Trajectory, ...]:
    if k < 0:
        return ()
    return ordered_plateau_anchors()[:k]


def active_anchor_vectors(
    k: int,
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        trajectory_vector(t.states)
        for t in active_anchor_subset(k)
    )


def mass_levels_with_saturation() -> tuple[int, ...]:
    return MASS_LEVELS + (SATURATION_MASS,)


__all__ = [
    "MASS_LEVELS", "PROBE_RADIUS", "SATURATION_MASS",
    "active_anchor_subset", "active_anchor_vectors",
    "mass_levels_with_saturation",
    "ordered_plateau_anchors",
]
