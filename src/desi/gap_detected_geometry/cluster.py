"""v3.47 — cohort assembly + cluster analysis.

Builds tail-aligned vectors for the four directive-
named cohorts:

* ``gap``       — terminal GAP cases (2)
* ``plateau``   — v3.31 plateau set (20)
* ``leakage``   — v3.43 leakage cohort (145)
* ``rescued``   — v3.30 cause-aware rescues (228)

Each cohort is reduced to a tuple of ``(trajectory_id,
tail_vector)`` pairs the report module uses to compute
nearest-manifold distances and 1-NN clusters.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..cause_aware_control.controller import control_all
from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..gap_detected.extractor import terminal_gap_cases
from ..plateau_separation.clustering import (
    connected_components, one_nn_edges,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .geometry import tail_vector


@dataclass(frozen=True)
class CohortMember:
    trajectory_id: str
    cohort: str           # "gap" | "plateau" | "leakage" | "rescued"
    vector: tuple[float, ...]


def _trajs_by_id() -> dict[str, Trajectory]:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def gap_members() -> tuple[CohortMember, ...]:
    trajs = _trajs_by_id()
    out: list[CohortMember] = []
    for c in terminal_gap_cases():
        t = trajs[c.trajectory_id]
        out.append(CohortMember(
            trajectory_id=c.trajectory_id,
            cohort="gap",
            vector=tail_vector(t.states),
        ))
    return tuple(out)


def plateau_members() -> tuple[CohortMember, ...]:
    trajs = _trajs_by_id()
    pids = plateau_trajectory_ids()
    out: list[CohortMember] = []
    for pid in pids:
        out.append(CohortMember(
            trajectory_id=pid, cohort="plateau",
            vector=tail_vector(trajs[pid].states),
        ))
    return tuple(out)


def leakage_members() -> tuple[CohortMember, ...]:
    return tuple(
        CohortMember(
            trajectory_id=t.trajectory_id,
            cohort="leakage",
            vector=tail_vector(t.states),
        )
        for t in collect_leakage_trajectories()
    )


def rescued_members() -> tuple[CohortMember, ...]:
    trajs = _trajs_by_id()
    out: list[CohortMember] = []
    for o in control_all():
        if not o.rescued:
            continue
        t = trajs[o.trajectory_id]
        out.append(CohortMember(
            trajectory_id=o.trajectory_id,
            cohort="rescued",
            vector=tail_vector(t.states),
        ))
    return tuple(out)


def gap_1nn_cluster_count() -> int:
    members = gap_members()
    vecs = tuple(m.vector for m in members)
    edges = one_nn_edges(vecs)
    return len(
        connected_components(len(vecs), edges),
    )


__all__ = [
    "CohortMember", "gap_1nn_cluster_count",
    "gap_members", "leakage_members",
    "plateau_members", "rescued_members",
]
