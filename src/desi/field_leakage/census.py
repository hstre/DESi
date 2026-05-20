"""v3.43 — leakage census.

Identifies every overcontrolled trajectory the v3.39
``frame_stability_condition`` policy produces on the
broader corpus and records, per trajectory:

* nearest-plateau distance and anchor id
* "same frame family", "same support family",
  "same pre-audit anchor_density" booleans
* nearest-overall neighbour (plateau or other leakage)
  for the ``nearest_neighbor_rate`` metric
* a closed machine-readable reason DESi attaches to
  its own action.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.state import StateVector
from ..plateau_specificity_recovery.policy import (
    apply_policy,
)
from ..plateau_specificity_recovery.selector import (
    SelectorKind, fires,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .distance import (
    euclidean, manifold_distance, per_state_dim_overlap,
    trajectory_vector,
)


_SUPPORTED = 4.0


# Closed reason set: every leakage case maps to exactly
# one. ``FRAME_FAMILY_AUDIT_WITHDRAWN`` is the
# structural reason for the 145 v3.39 leakages (shared
# frame anchor at index n-2, audit-step withdrawal
# overshoots).
_REASON_FRAME_FAMILY = "FRAME_FAMILY_AUDIT_WITHDRAWN"
_REASON_NON_FRAME    = "NON_FRAME_AUDIT_WITHDRAWN"


@dataclass(frozen=True)
class LeakageCase:
    trajectory_id: str
    nearest_plateau_id: str
    nn_distance_to_plateau: float
    same_frame_family: bool
    same_support_family: bool
    same_pre_audit_state: bool
    nearest_overall_id: str
    nearest_overall_is_plateau: bool
    machine_readable_reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "nearest_plateau_id":
                self.nearest_plateau_id,
            "nn_distance_to_plateau":
                self.nn_distance_to_plateau,
            "same_frame_family":
                self.same_frame_family,
            "same_support_family":
                self.same_support_family,
            "same_pre_audit_state":
                self.same_pre_audit_state,
            "nearest_overall_id":
                self.nearest_overall_id,
            "nearest_overall_is_plateau":
                self.nearest_overall_is_plateau,
            "machine_readable_reason":
                self.machine_readable_reason,
        }


def _gather_plateau_and_leakage() -> tuple[
    tuple[Trajectory, ...], tuple[Trajectory, ...],
]:
    pids = set(plateau_trajectory_ids())
    sel = SelectorKind.FRAME_STABILITY.value
    plateau: list[Trajectory] = []
    leakage: list[Trajectory] = []
    for t in extract_all_trajectories():
        if t.trajectory_id in pids:
            plateau.append(t)
            continue
        if not fires(sel, t.states):
            continue
        cf = apply_policy(t.states, sel)
        if (
            t.states[-1].support_state == _SUPPORTED
            and cf[-1].support_state != _SUPPORTED
        ):
            leakage.append(t)
    return tuple(plateau), tuple(leakage)


def _same_pre_audit_state(
    a: tuple[StateVector, ...], b: tuple[StateVector, ...],
) -> bool:
    """True when index n-2 state vectors are identical
    across every dimension."""
    return a[-2].to_dict() == b[-2].to_dict()


def collect_leakage_cases() -> tuple[LeakageCase, ...]:
    plateau, leakage = _gather_plateau_and_leakage()
    plat_vecs = [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in plateau
    ]
    leak_vecs = [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in leakage
    ]
    all_vecs = plat_vecs + leak_vecs
    plat_ids = {tid for tid, _ in plat_vecs}
    plat_by_id = {t.trajectory_id: t for t in plateau}
    plat_id_list = [tid for tid, _ in plat_vecs]
    out: list[LeakageCase] = []
    for t in leakage:
        vec = trajectory_vector(t.states)
        # nearest plateau
        d_plat, idx = manifold_distance(
            vec, tuple(v for _, v in plat_vecs),
        )
        nearest_pid = plat_id_list[idx] if idx >= 0 else ""
        # nearest overall (plateau or leakage),
        # excluding self
        best_d = float("inf")
        best_id = ""
        for tid, v in all_vecs:
            if tid == t.trajectory_id:
                continue
            d = euclidean(vec, v)
            if d < best_d:
                best_d = d
                best_id = tid
        # family booleans against the chosen nearest
        # plateau anchor
        anchor = plat_by_id[nearest_pid]
        frame_fam = per_state_dim_overlap(
            t.states, anchor.states, "frame_id",
            len(t.states) - 2,
        )
        supp_fam = per_state_dim_overlap(
            t.states, anchor.states, "support_state",
            len(t.states) - 2,
        )
        pre_audit = _same_pre_audit_state(
            t.states, anchor.states,
        )
        reason = (
            _REASON_FRAME_FAMILY if frame_fam
            else _REASON_NON_FRAME
        )
        out.append(LeakageCase(
            trajectory_id=t.trajectory_id,
            nearest_plateau_id=nearest_pid,
            nn_distance_to_plateau=round(d_plat, 6),
            same_frame_family=frame_fam,
            same_support_family=supp_fam,
            same_pre_audit_state=pre_audit,
            nearest_overall_id=best_id,
            nearest_overall_is_plateau=(
                best_id in plat_ids
            ),
            machine_readable_reason=reason,
        ))
    return tuple(out)


def collect_plateau_anchors() -> tuple[Trajectory, ...]:
    plateau, _ = _gather_plateau_and_leakage()
    return plateau


def collect_leakage_trajectories(
) -> tuple[Trajectory, ...]:
    _, leakage = _gather_plateau_and_leakage()
    return leakage


__all__ = [
    "LeakageCase", "collect_leakage_cases",
    "collect_leakage_trajectories",
    "collect_plateau_anchors",
]
