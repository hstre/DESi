"""v3.32 — plateau cause-structure report.

Pflichtmetriken (directive):

* ``plateau_cause_distribution`` — primary cause counts.
* ``plateau_cluster_count``      — number of clusters.
* ``dominant_plateau_class``     — single most common
  primary cause.
* ``intra_cluster_variance``     — sum of intra-cluster
  variances across all plateau clusters.

Killer question: are plateau trajectories homogeneous?
Reported as ``plateau_cluster_count == 1``.

Stop rule: ``plateau_nc_fp > 0.10`` halts the sprint.
NCs by construction have final_support == 4.0, so the
plateau-membership false-positive rate on NCs is 0.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from ..trajectory_control.negative_controls import all_ncs
from .cause_distribution import (
    CauseDistribution, collect_assignments,
    compute_distribution,
)
from .cluster import PlateauCluster, cluster
from .plateau_signals import (
    PlateauFeatures, extract_features,
)


MAX_PLATEAU_NC_FP                = 0.10


@dataclass(frozen=True)
class V332Report:
    plateau_count: int
    plateau_cause_distribution: dict[str, int]
    dominant_plateau_class: str | None
    multi_cause_count: int
    plateau_cluster_count: int
    intra_cluster_variance: float
    largest_cluster_size: int
    plateau_nc_fp_rate: float
    nc_count: int
    plateau_homogeneous: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "plateau_cause_distribution":
                dict(self.plateau_cause_distribution),
            "dominant_plateau_class":
                self.dominant_plateau_class,
            "multi_cause_count": self.multi_cause_count,
            "plateau_cluster_count":
                self.plateau_cluster_count,
            "intra_cluster_variance":
                self.intra_cluster_variance,
            "largest_cluster_size":
                self.largest_cluster_size,
            "plateau_nc_fp_rate":
                self.plateau_nc_fp_rate,
            "nc_count": self.nc_count,
            "plateau_homogeneous":
                self.plateau_homogeneous,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _plateau_features() -> tuple[PlateauFeatures, ...]:
    pids = set(plateau_trajectory_ids())
    return tuple(
        extract_features(t)
        for t in extract_all_trajectories()
        if t.trajectory_id in pids
    )


def build_report() -> V332Report:
    features = _plateau_features()
    trajs = extract_all_trajectories()
    assignments = collect_assignments(trajs)
    dist = compute_distribution(assignments)
    clusters = cluster(features)

    # NC plateau false-positive rate (final_support == 2.0)
    ncs = all_ncs()
    nc_plateau = sum(
        1 for n in ncs
        if n.trajectory.states[-1].support_state == 2.0
    )
    nc_rate = (
        round(nc_plateau / len(ncs), 6) if ncs else 0.0
    )

    cluster_count = len(clusters)
    intra_var = round(
        sum(c.intra_variance for c in clusters), 6,
    )
    largest = max(
        (c.size for c in clusters), default=0,
    )

    halt = nc_rate > MAX_PLATEAU_NC_FP
    if halt:
        verdict = "HALT_PLATEAU_NC_FP"
    elif cluster_count == 1:
        verdict = "PLATEAU_IS_HOMOGENEOUS"
    elif cluster_count >= 2:
        verdict = "PLATEAU_HAS_SUBTYPES"
    else:
        verdict = "PLATEAU_EMPTY"

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"plateau_nc_fp_rate {nc_rate} <= "
        f"{MAX_PLATEAU_NC_FP}",
        f"INFO: plateau_cluster_count {cluster_count}",
        f"INFO: dominant_plateau_class "
        f"{dist.dominant_primary}",
        f"INFO: multi_cause_count {dist.multi_cause_count}",
        f"INFO: largest_cluster_size {largest} "
        f"of {len(features)}",
    )

    return V332Report(
        plateau_count=len(features),
        plateau_cause_distribution=dict(dist.primary),
        dominant_plateau_class=dist.dominant_primary,
        multi_cause_count=dist.multi_cause_count,
        plateau_cluster_count=cluster_count,
        intra_cluster_variance=intra_var,
        largest_cluster_size=largest,
        plateau_nc_fp_rate=nc_rate,
        nc_count=len(ncs),
        plateau_homogeneous=(cluster_count == 1),
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cause_map_artifact() -> dict[str, object]:
    trajs = extract_all_trajectories()
    assignments = collect_assignments(trajs)
    return {
        "schema_version": "v3_32_plateau_cause_map",
        "assignments": [a.to_dict() for a in assignments],
    }


def build_clusters_artifact() -> dict[str, object]:
    features = _plateau_features()
    clusters = cluster(features)
    return {
        "schema_version": "v3_32_plateau_clusters",
        "features": [f.to_dict() for f in features],
        "clusters": [c.to_dict() for c in clusters],
    }


__all__ = [
    "MAX_PLATEAU_NC_FP", "V332Report",
    "build_cause_map_artifact",
    "build_clusters_artifact", "build_report",
]
