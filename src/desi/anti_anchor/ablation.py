"""v3.51 — anti-anchor-modulated radius sweep.

For each AntiAnchorKind, run a v3.44-style radius
gate at ``PLATEAU_RADIUS`` with the modification that
firing additionally requires the trajectory to be
FARTHER than ``ANTI_RADIUS`` from every selected anti-
anchor. Per (kind, trajectory), emit an AntiOutcome
recording resolve / leakage / repulsion.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.census import collect_plateau_anchors
from ..field_leakage.distance import (
    euclidean, manifold_distance, trajectory_vector,
)
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .anchors import (
    ANTI_COUNT, ANTI_RADIUS, AntiAnchorKind,
    anti_anchor_vectors,
)


PLATEAU_RADIUS: float = 4.0
_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0


@dataclass(frozen=True)
class AntiOutcome:
    trajectory_id: str
    anti_kind: str
    is_plateau: bool
    near_plateau: bool
    near_any_anti: bool
    selector_fired: bool
    repelled: bool                # would have fired
                                  # without anti
    original_final_support: float
    counterfactual_final_support: float
    plateau_resolved: bool
    leakage: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "anti_kind": self.anti_kind,
            "is_plateau": self.is_plateau,
            "near_plateau": self.near_plateau,
            "near_any_anti": self.near_any_anti,
            "selector_fired": self.selector_fired,
            "repelled": self.repelled,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "plateau_resolved": self.plateau_resolved,
            "leakage": self.leakage,
        }


def _outcome(
    traj: Trajectory, kind: str,
    plat_vecs: tuple[tuple[float, ...], ...],
    anti_vecs: tuple[tuple[float, ...], ...],
    plateau_ids: set,
) -> AntiOutcome:
    vec = trajectory_vector(traj.states)
    d_plat, _ = manifold_distance(vec, plat_vecs)
    near_plat = d_plat <= PLATEAU_RADIUS
    if anti_vecs:
        d_anti, _ = manifold_distance(vec, anti_vecs)
        near_anti = d_anti <= ANTI_RADIUS
    else:
        near_anti = False
    fired = near_plat and not near_anti
    repelled = near_plat and near_anti
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
    return AntiOutcome(
        trajectory_id=traj.trajectory_id,
        anti_kind=kind, is_plateau=is_plateau,
        near_plateau=near_plat,
        near_any_anti=near_anti,
        selector_fired=fired, repelled=repelled,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        plateau_resolved=resolved, leakage=leak,
    )


def run_under_anti(
    kind: str,
) -> tuple[AntiOutcome, ...]:
    pids = set(plateau_trajectory_ids())
    plat_vecs = tuple(
        trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    )
    anti_vecs = anti_anchor_vectors(kind, ANTI_COUNT)
    return tuple(
        _outcome(
            t, kind, plat_vecs, anti_vecs, pids,
        )
        for t in extract_all_trajectories()
    )


def run_all_anti_kinds() -> tuple[AntiOutcome, ...]:
    out: list[AntiOutcome] = []
    for k in AntiAnchorKind:
        out.extend(run_under_anti(k.value))
    return tuple(out)


__all__ = [
    "AntiOutcome", "PLATEAU_RADIUS",
    "run_all_anti_kinds", "run_under_anti",
]
