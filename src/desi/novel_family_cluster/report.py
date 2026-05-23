"""v3.86 — blind doppelganger detection report on
novel families.

Pflichtmetriken (directive § v3.86):

* ``predicted_cluster_count``
* ``cluster_purity``
* ``cluster_recall``
* ``distance_gap``
* ``replay_stability``

Concept gate (§ v3.86): cluster_purity ≥ 0.70 AND
cluster_recall ≥ 0.70. Killerfrage: "Entstehen
Doppelganger auch in unbekannten Familien?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..novel_families import all_family_members
from .cluster import (
    all_novel_blind_clusters,
    cluster_purity, cluster_recall,
    cluster_sizes, predicted_cluster_count,
)
from .distance import (
    novel_distance_gap,
    novel_pairwise_distances,
)


PURITY_THRESHOLD: float = 0.70
RECALL_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V386Report:
    anchor_count: int
    predicted_cluster_count: int
    cluster_sizes: tuple[int, ...]
    cluster_purity: float
    cluster_recall: float
    distance_gap: float
    pairwise_distance_count: int
    clusters: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "anchor_count": self.anchor_count,
            "predicted_cluster_count":
                self.predicted_cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "cluster_purity": self.cluster_purity,
            "cluster_recall": self.cluster_recall,
            "distance_gap": self.distance_gap,
            "pairwise_distance_count":
                self.pairwise_distance_count,
            "clusters": list(self.clusters),
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
    a = [
        c.to_dict()
        for c in all_novel_blind_clusters()
    ]
    b = [
        c.to_dict()
        for c in all_novel_blind_clusters()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V386Report:
    clusters = all_novel_blind_clusters()
    dists = novel_pairwise_distances()
    gap = novel_distance_gap()
    sizes = cluster_sizes(clusters)
    purity = cluster_purity(clusters)
    recall = cluster_recall(clusters)
    replay = _replay_stability()
    anchor_count = sum(
        len(ms) for ms in all_family_members().values()
    )

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        purity >= PURITY_THRESHOLD
        and recall >= RECALL_THRESHOLD
    ):
        verdict = "NOVEL_DOPPELGAENGER_DETECTED"
    elif purity >= PURITY_THRESHOLD:
        verdict = "NOVEL_DOPPELGAENGER_PARTIAL"
    else:
        verdict = "NOVEL_DOPPELGAENGER_NOT_DETECTED"

    rationale = (
        f"INFO: anchor_count {anchor_count}",
        f"INFO: distance_gap {gap}",
        f"INFO: pairwise_distance_count "
        f"{len(dists)}",
        f"INFO: predicted_cluster_count "
        f"{len(clusters)}",
        f"INFO: cluster_sizes {list(sizes)}",
        f"{'PASS' if purity >= PURITY_THRESHOLD else 'FAIL'}: "
        f"cluster_purity {purity} "
        f"(threshold {PURITY_THRESHOLD})",
        f"{'PASS' if recall >= RECALL_THRESHOLD else 'FAIL'}: "
        f"cluster_recall {recall} "
        f"(threshold {RECALL_THRESHOLD})",
        f"INFO: clusters "
        f"{[c.to_dict() for c in clusters]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V386Report(
        anchor_count=anchor_count,
        predicted_cluster_count=len(clusters),
        cluster_sizes=sizes,
        cluster_purity=purity,
        cluster_recall=recall,
        distance_gap=gap,
        pairwise_distance_count=len(dists),
        clusters=tuple(
            c.to_dict() for c in clusters
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_novel_family_clusters_artifact(
) -> dict[str, object]:
    clusters = all_novel_blind_clusters()
    dists = novel_pairwise_distances()
    gap = novel_distance_gap()
    return {
        "schema_version":
            "v3_86_novel_family_clusters",
        "anchor_count": sum(
            len(ms)
            for ms in all_family_members().values()
        ),
        "distance_gap": gap,
        "pairwise_distance_count": len(dists),
        "clusters": [
            c.to_dict() for c in clusters
        ],
        "pairwise_distances": [
            {"a": a, "b": b, "distance": d}
            for a, b, d in dists
        ],
    }


__all__ = [
    "PURITY_THRESHOLD", "RECALL_THRESHOLD",
    "V386Report",
    "build_novel_family_clusters_artifact",
    "build_report",
]
