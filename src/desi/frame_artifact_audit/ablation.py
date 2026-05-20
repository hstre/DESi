"""v3.49 — radius sweep under each mask.

For every (mask, radius) pair from the closed sets,
mask plateau anchors AND test trajectories uniformly
and rerun the v3.44 radius-bounded selector. Tally
plateau_recall and leakage_count exactly as in
v3.44 so the radius_break_after_mask comparison is
direct.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.census import collect_plateau_anchors
from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)
from ..field_radius_sweep.radius import (
    RADII, radius_label,
)
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .mask import (
    MaskKind, apply_mask, build_permutation_table,
)


_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0


@dataclass(frozen=True)
class MaskedOutcome:
    trajectory_id: str
    mask: str
    radius_label: str
    is_plateau: bool
    selector_fired: bool
    original_final_support: float
    plateau_resolved: bool
    leakage: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "mask": self.mask,
            "radius_label": self.radius_label,
            "is_plateau": self.is_plateau,
            "selector_fired": self.selector_fired,
            "original_final_support":
                self.original_final_support,
            "plateau_resolved":
                self.plateau_resolved,
            "leakage": self.leakage,
        }


def _masked_states(
    traj: Trajectory, mask: str,
    permutation_table: dict,
) -> tuple:
    seq = (
        permutation_table.get(traj.trajectory_id)
        if mask == MaskKind.FRAME_PERMUTED.value
        else None
    )
    return apply_mask(traj.states, mask, seq)


def _apply_at(
    traj: Trajectory, mask: str, radius: float,
    plat_vecs: tuple[tuple[float, ...], ...],
    plateau_ids: set, permutation_table: dict,
) -> MaskedOutcome:
    masked = _masked_states(
        traj, mask, permutation_table,
    )
    vec = trajectory_vector(masked)
    if radius < 0:
        fired = False
    else:
        d, _ = manifold_distance(vec, plat_vecs)
        fired = d <= radius
    # The intervention itself (apply_k_holds) operates
    # on the ORIGINAL states - masking changes only
    # the selector's input, not the trajectory's
    # actual support trace. That isolates "does the
    # selector still discriminate?" from "does the
    # intervention still work?".
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
    return MaskedOutcome(
        trajectory_id=traj.trajectory_id,
        mask=mask,
        radius_label=radius_label(radius),
        is_plateau=is_plateau,
        selector_fired=fired,
        original_final_support=orig_final,
        plateau_resolved=resolved, leakage=leak,
    )


def run_under_mask(
    mask: str, radius: float,
) -> tuple[MaskedOutcome, ...]:
    pids = set(plateau_trajectory_ids())
    trajs = tuple(extract_all_trajectories())
    permutation = build_permutation_table(trajs)
    # Mask plateau anchors with the same transformation
    plat_anchors = collect_plateau_anchors()
    plat_vecs = tuple(
        trajectory_vector(
            _masked_states(t, mask, permutation),
        )
        for t in plat_anchors
    )
    return tuple(
        _apply_at(
            t, mask, radius, plat_vecs, pids,
            permutation,
        )
        for t in trajs
    )


def run_all_combinations() -> tuple[MaskedOutcome, ...]:
    masks = [k.value for k in MaskKind]
    out: list[MaskedOutcome] = []
    for m in masks:
        for r in RADII:
            out.extend(run_under_mask(m, r))
    return tuple(out)


__all__ = [
    "MaskedOutcome", "run_all_combinations",
    "run_under_mask",
]
