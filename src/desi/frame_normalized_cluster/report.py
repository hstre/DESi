"""v3.90 — frame-normalized clustering report.

Pflichtmetriken (directive § v3.90):

* ``normalized_cluster_count``
* ``normalized_cluster_purity``
* ``normalized_cluster_recall``
* ``normalized_distance_gap``
* ``replay_stability``

Concept Gate condition #2: normalized_cluster_purity
>= 0.70. Killerfrage: "Kommt Doppelganger-Geometrie
nach Frame-Normalisierung zurueck?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..novel_family_cluster.cluster import (
    cluster_purity as baseline_purity_fn,
    all_novel_blind_clusters,
)
from .cluster import (
    all_normalized_clusters,
    normalized_cluster_count,
    normalized_cluster_purity,
    normalized_cluster_recall,
    normalized_cluster_sizes,
    normalized_distance_gap,
    normalized_pairwise_distances,
)


PURITY_THRESHOLD: float = 0.70
RECALL_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V390Report:
    baseline_purity: float
    normalized_cluster_count: int
    normalized_cluster_sizes: tuple[int, ...]
    normalized_cluster_purity: float
    normalized_cluster_recall: float
    normalized_distance_gap: float
    purity_delta: float
    clusters: tuple[dict, ...]
    pairwise_distance_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_purity":
                self.baseline_purity,
            "normalized_cluster_count":
                self.normalized_cluster_count,
            "normalized_cluster_sizes":
                list(self.normalized_cluster_sizes),
            "normalized_cluster_purity":
                self.normalized_cluster_purity,
            "normalized_cluster_recall":
                self.normalized_cluster_recall,
            "normalized_distance_gap":
                self.normalized_distance_gap,
            "purity_delta": self.purity_delta,
            "clusters": list(self.clusters),
            "pairwise_distance_count":
                self.pairwise_distance_count,
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


def _baseline_purity() -> float:
    return baseline_purity_fn(
        all_novel_blind_clusters(),
    )


def _replay_stability() -> float:
    a = (
        normalized_cluster_purity(),
        normalized_cluster_recall(),
        normalized_distance_gap(),
    )
    b = (
        normalized_cluster_purity(),
        normalized_cluster_recall(),
        normalized_distance_gap(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V390Report:
    base = _baseline_purity()
    nc = normalized_cluster_count()
    ns = normalized_cluster_sizes()
    np = normalized_cluster_purity()
    nr = normalized_cluster_recall()
    ng = normalized_distance_gap()
    clusters = all_normalized_clusters()
    dists = normalized_pairwise_distances()
    delta = _round(np - base)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        np >= PURITY_THRESHOLD
        and nr >= RECALL_THRESHOLD
    ):
        verdict = "DOPPELGAENGER_RECOVERED"
    elif np >= PURITY_THRESHOLD:
        verdict = "DOPPELGAENGER_PARTIAL_RECOVERY"
    elif np > base:
        verdict = "DOPPELGAENGER_WEAK_RECOVERY"
    else:
        verdict = "DOPPELGAENGER_NOT_RECOVERED"

    rationale = (
        f"INFO: baseline_purity {base}",
        f"INFO: normalized_cluster_count {nc}",
        f"INFO: normalized_cluster_sizes "
        f"{list(ns)}",
        f"{'PASS' if np >= PURITY_THRESHOLD else 'FAIL'}: "
        f"normalized_cluster_purity {np} "
        f"(threshold {PURITY_THRESHOLD})",
        f"{'PASS' if nr >= RECALL_THRESHOLD else 'FAIL'}: "
        f"normalized_cluster_recall {nr} "
        f"(threshold {RECALL_THRESHOLD})",
        f"INFO: normalized_distance_gap {ng}",
        f"INFO: purity_delta {delta} "
        f"(normalized minus baseline)",
        f"INFO: clusters "
        f"{[c.to_dict() for c in clusters]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V390Report(
        baseline_purity=base,
        normalized_cluster_count=nc,
        normalized_cluster_sizes=ns,
        normalized_cluster_purity=np,
        normalized_cluster_recall=nr,
        normalized_distance_gap=ng,
        purity_delta=delta,
        clusters=tuple(
            c.to_dict() for c in clusters
        ),
        pairwise_distance_count=len(dists),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_frame_normalized_clusters_artifact(
) -> dict[str, object]:
    clusters = all_normalized_clusters()
    dists = normalized_pairwise_distances()
    return {
        "schema_version":
            "v3_90_frame_normalized_clusters",
        "normalized_distance_gap":
            normalized_distance_gap(),
        "normalized_cluster_count":
            normalized_cluster_count(),
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
    "V390Report",
    "build_frame_normalized_clusters_artifact",
    "build_report",
]
