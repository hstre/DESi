"""v3.44 — radius-sweep ablation.

For each closed radius in ``RADII`` and every
trajectory in the corpus, decide whether the
radius-gated policy fires, apply Strategy B if it
does, and tally:

* ``plateau_resolved`` — plateau case moved off 2.0
* ``leakage``          — SUPPORTED non-plateau case
  moved off 4.0
* ``selector_fired``   — selector accepted the case

The ablation runs against the FULL corpus, not the
v3.35 cliff-class universe, because the leakage
metric is defined corpus-wide (v3.43 finding).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.census import collect_plateau_anchors
from ..field_leakage.distance import trajectory_vector
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .radius import (
    RADII, radius_label, selector_for_radius,
)


_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0


@dataclass(frozen=True)
class RadiusOutcome:
    trajectory_id: str
    radius_label: str
    is_plateau: bool
    selector_fired: bool
    original_final_support: float
    counterfactual_final_support: float
    plateau_resolved: bool
    leakage: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "radius_label": self.radius_label,
            "is_plateau": self.is_plateau,
            "selector_fired": self.selector_fired,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "plateau_resolved": self.plateau_resolved,
            "leakage": self.leakage,
        }


def _apply_at_radius(
    traj: Trajectory, radius: float,
    plat_vecs: tuple[tuple[float, ...], ...],
    plateau_ids: set,
) -> RadiusOutcome:
    fired = selector_for_radius(
        traj.states, radius, plat_vecs,
    )
    cf = (
        apply_k_holds(traj.states, 1)
        if fired else traj.states
    )
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    is_plateau = traj.trajectory_id in plateau_ids
    resolved = (
        is_plateau
        and orig_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
        and fired
    )
    leak = (
        not is_plateau
        and orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
        and fired
    )
    return RadiusOutcome(
        trajectory_id=traj.trajectory_id,
        radius_label=radius_label(radius),
        is_plateau=is_plateau, selector_fired=fired,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        plateau_resolved=resolved, leakage=leak,
    )


def run_at_radius(
    radius: float,
) -> tuple[RadiusOutcome, ...]:
    pids = set(plateau_trajectory_ids())
    plat_vecs = tuple(
        trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    )
    trajs = extract_all_trajectories()
    return tuple(
        _apply_at_radius(t, radius, plat_vecs, pids)
        for t in trajs
    )


def run_all_radii() -> tuple[RadiusOutcome, ...]:
    out: list[RadiusOutcome] = []
    for r in RADII:
        out.extend(run_at_radius(r))
    return tuple(out)


__all__ = [
    "RadiusOutcome", "run_all_radii", "run_at_radius",
]
