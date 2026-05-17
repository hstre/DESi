"""v3.81 — blind equivalence detection report.

Pflichtmetriken (directive § v3.81):

* ``predicted_cluster_count``
* ``cluster_sizes``
* ``cluster_purity``
* ``cluster_recall``
* ``replay_stability``

Stop rule: ``cluster_purity < 0.70`` → hypothesis
weak, document but continue. Killerfrage: "Sieht
DESi Doppelganger ohne Ablation?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..redundancy_masking.equivalence import (
    PROBE_RADIUS, redundancy_classes,
)
from .blind_cluster import (
    cluster_class_matches, cluster_purity,
    cluster_recall, cluster_sizes,
    predicted_cluster_count,
)
from .equivalence import (
    all_blind_clusters, largest_gap_threshold,
    pairwise_distances, plateau_anchor_vectors,
)


PURITY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V381Report:
    probe_radius: float
    cluster_threshold: float
    predicted_cluster_count: int
    cluster_sizes: tuple[int, ...]
    cluster_purity: float
    cluster_recall: float
    clusters: tuple[dict, ...]
    cluster_class_matches: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "cluster_threshold":
                self.cluster_threshold,
            "predicted_cluster_count":
                self.predicted_cluster_count,
            "cluster_sizes":
                list(self.cluster_sizes),
            "cluster_purity": self.cluster_purity,
            "cluster_recall": self.cluster_recall,
            "clusters": list(self.clusters),
            "cluster_class_matches":
                list(self.cluster_class_matches),
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
    a = [c.to_dict() for c in all_blind_clusters()]
    b = [c.to_dict() for c in all_blind_clusters()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V381Report:
    vecs = plateau_anchor_vectors()
    dists = pairwise_distances(vecs)
    threshold = largest_gap_threshold(dists)
    clusters = all_blind_clusters()
    classes = redundancy_classes()
    matches = cluster_class_matches(
        clusters, classes,
    )
    sizes = cluster_sizes(clusters)
    purity = cluster_purity(clusters, classes)
    recall = cluster_recall(clusters, classes)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif purity >= PURITY_THRESHOLD:
        verdict = "DOPPELGAENGER_DETECTED_BLIND"
    else:
        verdict = "DOPPELGAENGER_HYPOTHESIS_WEAK"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: cluster_threshold "
        f"{threshold} (largest-gap midpoint)",
        f"INFO: predicted_cluster_count "
        f"{len(clusters)}",
        f"INFO: cluster_sizes {list(sizes)}",
        f"{'PASS' if purity >= PURITY_THRESHOLD else 'FAIL'}: "
        f"cluster_purity {purity} "
        f"(threshold {PURITY_THRESHOLD})",
        f"INFO: cluster_recall {recall}",
        f"INFO: clusters "
        f"{[c.to_dict() for c in clusters]}",
        f"INFO: cluster_class_matches "
        f"{[m.to_dict() for m in matches]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V381Report(
        probe_radius=PROBE_RADIUS,
        cluster_threshold=threshold,
        predicted_cluster_count=len(clusters),
        cluster_sizes=sizes,
        cluster_purity=purity,
        cluster_recall=recall,
        clusters=tuple(
            c.to_dict() for c in clusters
        ),
        cluster_class_matches=tuple(
            m.to_dict() for m in matches
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_blind_equivalence_clusters_artifact(
) -> dict[str, object]:
    vecs = plateau_anchor_vectors()
    dists = pairwise_distances(vecs)
    threshold = largest_gap_threshold(dists)
    clusters = all_blind_clusters()
    return {
        "schema_version":
            "v3_81_blind_equivalence_clusters",
        "probe_radius": PROBE_RADIUS,
        "cluster_threshold": threshold,
        "anchor_count": len(vecs),
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
    "PURITY_THRESHOLD",
    "V381Report",
    "build_blind_equivalence_clusters_artifact",
    "build_report",
]
