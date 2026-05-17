"""v3.76 — blind recovery report.

Pflichtmetriken (directive § v3.76):

* ``missing_count_error``
* ``region_recall``
* ``role_recall``
* ``false_reconstruction_rate``
* ``replay_stability``

Neptun concept gate #4:
``region_recall >= 0.70``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .blind import (
    CLUSTER_DISTANCE_THRESHOLD, HIDDEN_ROLES,
    HIDDEN_SUBSET, cluster_orphans,
    orphan_indices, visible_set,
)
from .recover import (
    assign_clusters, false_reconstruction_rate,
    missing_count_error,
    predicted_distinct_regions,
    region_recall, role_recall,
)


NEPTUN_REGION_RECALL_FLOOR: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V376Report:
    hidden_subset: tuple[str, ...]
    visible_set: tuple[str, ...]
    orphan_count: int
    cluster_count: int
    cluster_assignments: tuple[dict, ...]
    missing_count_error: int
    region_recall: float
    role_recall: float
    false_reconstruction_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "hidden_subset":
                list(self.hidden_subset),
            "visible_set":
                list(self.visible_set),
            "orphan_count": self.orphan_count,
            "cluster_count": self.cluster_count,
            "cluster_assignments":
                list(self.cluster_assignments),
            "missing_count_error":
                self.missing_count_error,
            "region_recall": self.region_recall,
            "role_recall": self.role_recall,
            "false_reconstruction_rate":
                self.false_reconstruction_rate,
            "replay_stability":
                self.replay_stability,
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
    a = [a.to_dict() for a in assign_clusters()]
    b = [a.to_dict() for a in assign_clusters()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V376Report:
    assignments = assign_clusters()
    clusters = cluster_orphans()
    orphans = orphan_indices()
    err = missing_count_error(assignments)
    rec_r = region_recall(assignments)
    role_r = role_recall(assignments)
    false_r = false_reconstruction_rate(assignments)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rec_r >= NEPTUN_REGION_RECALL_FLOOR:
        verdict = "BLIND_RECOVERY_USABLE"
    elif rec_r > 0:
        verdict = "BLIND_RECOVERY_WEAK"
    else:
        verdict = "BLIND_RECOVERY_FAILED"

    rationale = (
        f"INFO: hidden_subset "
        f"{list(HIDDEN_SUBSET)} (roles "
        f"{sorted(HIDDEN_ROLES.items())})",
        f"INFO: visible_set {list(visible_set())}",
        f"INFO: orphan_count {len(orphans)}",
        f"INFO: cluster_count {len(clusters)}",
        f"INFO: cluster_assignments "
        f"{[a.to_dict() for a in assignments]}",
        f"INFO: missing_count_error {err} "
        f"(distinct regions; HIGH+REDUNDANT cover "
        f"identical leakages so they count as one)",
        f"{'PASS' if rec_r >= NEPTUN_REGION_RECALL_FLOOR else 'FAIL'}: "
        f"region_recall {rec_r} >= "
        f"{NEPTUN_REGION_RECALL_FLOOR}",
        f"INFO: role_recall {role_r}",
        f"INFO: false_reconstruction_rate {false_r}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V376Report(
        hidden_subset=HIDDEN_SUBSET,
        visible_set=visible_set(),
        orphan_count=len(orphans),
        cluster_count=len(clusters),
        cluster_assignments=tuple(
            a.to_dict() for a in assignments
        ),
        missing_count_error=err,
        region_recall=rec_r,
        role_recall=role_r,
        false_reconstruction_rate=false_r,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_blind_recovery_artifact(
) -> dict[str, object]:
    assignments = assign_clusters()
    return {
        "schema_version":
            "v3_76_blind_recovery",
        "cluster_distance_threshold":
            CLUSTER_DISTANCE_THRESHOLD,
        "hidden_subset": list(HIDDEN_SUBSET),
        "hidden_roles":
            dict(sorted(HIDDEN_ROLES.items())),
        "visible_set": list(visible_set()),
        "cluster_assignments": [
            a.to_dict() for a in assignments
        ],
    }


__all__ = [
    "NEPTUN_REGION_RECALL_FLOOR", "V376Report",
    "build_blind_recovery_artifact",
    "build_report",
]
