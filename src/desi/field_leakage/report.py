"""v3.43 — leakage census report.

Pflichtmetriken (directive):

* ``leakage_count``               — total cases.
* ``mean_manifold_distance``      — average minimum
  Euclidean distance from a leakage trajectory to the
  plateau manifold (the 20 plateau trajectories).
* ``leakage_cluster_count``       — connected
  components in the 1-NN graph restricted to the
  leakage cohort.
* ``nearest_neighbor_rate``       — fraction of
  leakage cases whose nearest overall neighbour
  (in plateau ∪ leakage) is a plateau case.
* ``explanation_replay_stability``

Stop rule (directive): explanation_replay_stability < 1
halts the sprint.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..plateau_separation.clustering import (
    connected_components, one_nn_edges,
)
from .census import (
    LeakageCase, collect_leakage_cases,
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from .distance import trajectory_vector


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V343Report:
    plateau_count: int
    leakage_count: int
    mean_manifold_distance: float
    min_manifold_distance: float
    max_manifold_distance: float
    leakage_cluster_count: int
    largest_cluster_size: int
    nearest_neighbor_rate: float
    same_frame_family_rate: float
    same_support_family_rate: float
    reason_distribution: dict[str, int]
    explanation_replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "leakage_count": self.leakage_count,
            "mean_manifold_distance":
                self.mean_manifold_distance,
            "min_manifold_distance":
                self.min_manifold_distance,
            "max_manifold_distance":
                self.max_manifold_distance,
            "leakage_cluster_count":
                self.leakage_cluster_count,
            "largest_cluster_size":
                self.largest_cluster_size,
            "nearest_neighbor_rate":
                self.nearest_neighbor_rate,
            "same_frame_family_rate":
                self.same_frame_family_rate,
            "same_support_family_rate":
                self.same_support_family_rate,
            "reason_distribution":
                dict(self.reason_distribution),
            "explanation_replay_stability":
                self.explanation_replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = [c.to_dict() for c in collect_leakage_cases()]
    b = [c.to_dict() for c in collect_leakage_cases()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V343Report:
    cases = collect_leakage_cases()
    plateau = collect_plateau_anchors()
    leakage = collect_leakage_trajectories()

    if cases:
        dists = [c.nn_distance_to_plateau for c in cases]
        mean_d = _round(sum(dists) / len(dists))
        min_d = _round(min(dists))
        max_d = _round(max(dists))
        nn_rate = _round(
            sum(
                1 for c in cases
                if c.nearest_overall_is_plateau
            ) / len(cases),
        )
        ff_rate = _round(
            sum(
                1 for c in cases if c.same_frame_family
            ) / len(cases),
        )
        sf_rate = _round(
            sum(
                1 for c in cases
                if c.same_support_family
            ) / len(cases),
        )
    else:
        mean_d = min_d = max_d = 0.0
        nn_rate = ff_rate = sf_rate = 0.0

    leak_vecs = tuple(
        trajectory_vector(t.states) for t in leakage
    )
    edges = one_nn_edges(leak_vecs)
    components = connected_components(
        len(leak_vecs), edges,
    )
    cluster_count = len(components)
    largest = max(
        (len(c) for c in components), default=0,
    )

    reasons = dict(Counter(
        c.machine_readable_reason for c in cases
    ))

    replay = _replay_stability()
    halt = replay < 1.0
    if halt:
        verdict = "HALT_EXPLANATION_REPLAY_DRIFT"
    elif nn_rate == 0.0:
        verdict = "LEAKAGE_FORMS_OWN_MANIFOLD"
    else:
        verdict = "LEAKAGE_BORDERS_PLATEAU"

    rationale = (
        f"INFO: leakage_count {len(cases)}",
        f"INFO: mean_manifold_distance {mean_d} "
        f"(range {min_d}..{max_d})",
        f"INFO: leakage_cluster_count {cluster_count} "
        f"(largest {largest})",
        f"INFO: nearest_neighbor_rate {nn_rate} "
        f"(fraction of leakage whose 1-NN is a plateau)",
        f"INFO: same_frame_family_rate {ff_rate}, "
        f"same_support_family_rate {sf_rate}",
        f"INFO: reason_distribution {sorted(reasons.items())}",
        f"{'PASS' if not halt else 'FAIL'}: "
        f"explanation_replay_stability {replay}",
    )

    return V343Report(
        plateau_count=len(plateau),
        leakage_count=len(cases),
        mean_manifold_distance=mean_d,
        min_manifold_distance=min_d,
        max_manifold_distance=max_d,
        leakage_cluster_count=cluster_count,
        largest_cluster_size=largest,
        nearest_neighbor_rate=nn_rate,
        same_frame_family_rate=ff_rate,
        same_support_family_rate=sf_rate,
        reason_distribution=reasons,
        explanation_replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_leakage_inventory_artifact(
) -> dict[str, object]:
    cases = collect_leakage_cases()
    return {
        "schema_version": "v3_43_leakage_inventory",
        "cases": [c.to_dict() for c in cases],
        "case_count": len(cases),
    }


def build_manifold_distance_map_artifact(
) -> dict[str, object]:
    """Per (leakage_id, plateau_id) Euclidean distance
    matrix - used by v3.44 radius sweep to define
    inclusion balls."""
    plateau = collect_plateau_anchors()
    leakage = collect_leakage_trajectories()
    plat_vecs = [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in plateau
    ]
    rows = []
    for t in leakage:
        v = trajectory_vector(t.states)
        from .distance import euclidean
        rows.append({
            "trajectory_id": t.trajectory_id,
            "distances": {
                pid: round(euclidean(v, pv), 6)
                for pid, pv in plat_vecs
            },
        })
    return {
        "schema_version": "v3_43_manifold_distance_map",
        "plateau_anchors": [
            t.trajectory_id for t in plateau
        ],
        "rows": rows,
    }


__all__ = [
    "V343Report", "build_leakage_inventory_artifact",
    "build_manifold_distance_map_artifact",
    "build_report",
]
