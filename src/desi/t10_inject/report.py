"""v3.102 — T10 single-dimension injection report.

Pflichtmetriken (directive § v3.102):

* ``injected_purity``
* ``injected_auc``
* ``geometry_delta``
* ``cluster_delta``
* ``replay_stability``

Concept Gate conditions #2/#3: injected_purity >=
0.70 AND injected_auc >= 0.70. Killerfrage:
"Reicht eine einzige zusaetzliche Dimension?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .inject import (
    baseline_dim, injected_dim,
    injected_vectors,
    selected_candidate,
)
from .recover import (
    all_injected_clusters,
    cluster_delta,
    geometry_delta,
    injected_auc,
    injected_cluster_count,
    injected_cluster_sizes,
    injected_purity,
)


PURITY_THRESHOLD: float = 0.70
AUC_THRESHOLD: float = 0.70
GEOMETRY_DELTA_TOLERANCE: float = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3102Report:
    entangled_family_ids: tuple[str, ...]
    selected_candidate: str
    baseline_dim: int
    injected_dim: int
    injected_cluster_count: int
    injected_cluster_sizes: tuple[int, ...]
    injected_purity: float
    injected_auc: float
    geometry_delta: float
    cluster_delta: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "selected_candidate":
                self.selected_candidate,
            "baseline_dim": self.baseline_dim,
            "injected_dim": self.injected_dim,
            "injected_cluster_count":
                self.injected_cluster_count,
            "injected_cluster_sizes":
                list(
                    self.injected_cluster_sizes,
                ),
            "injected_purity":
                self.injected_purity,
            "injected_auc": self.injected_auc,
            "geometry_delta":
                self.geometry_delta,
            "cluster_delta":
                self.cluster_delta,
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
    a = (
        injected_purity(), injected_auc(),
        geometry_delta(), cluster_delta(),
        selected_candidate(),
    )
    b = (
        injected_purity(), injected_auc(),
        geometry_delta(), cluster_delta(),
        selected_candidate(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3102Report:
    cand = selected_candidate()
    purity = injected_purity()
    auc = injected_auc()
    gd = geometry_delta()
    cd = cluster_delta()
    bd = baseline_dim()
    id_ = injected_dim()
    cluster_count = injected_cluster_count()
    cluster_sizes = injected_cluster_sizes()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        purity >= PURITY_THRESHOLD
        and auc >= AUC_THRESHOLD
    ):
        verdict = "SINGLE_DIM_RESCUES"
    elif (
        purity >= PURITY_THRESHOLD
        or auc >= AUC_THRESHOLD
    ):
        verdict = "SINGLE_DIM_PARTIAL"
    else:
        verdict = "SINGLE_DIM_INSUFFICIENT"

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"INFO: selected_candidate {cand}",
        f"INFO: baseline_dim {bd} "
        f"injected_dim {id_} (delta=+1)",
        f"INFO: injected_cluster_count "
        f"{cluster_count} sizes "
        f"{list(cluster_sizes)}",
        f"{'PASS' if purity >= PURITY_THRESHOLD else 'FAIL'}: "
        f"injected_purity {purity} "
        f"(threshold {PURITY_THRESHOLD})",
        f"{'PASS' if auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"injected_auc {auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: geometry_delta {gd} "
        f"(tolerance "
        f"{GEOMETRY_DELTA_TOLERANCE})",
        f"INFO: cluster_delta {cd}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3102Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        selected_candidate=cand,
        baseline_dim=bd,
        injected_dim=id_,
        injected_cluster_count=cluster_count,
        injected_cluster_sizes=cluster_sizes,
        injected_purity=purity,
        injected_auc=auc,
        geometry_delta=gd,
        cluster_delta=cd,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_single_dimension_injection_artifact(
) -> dict[str, object]:
    clusters = all_injected_clusters()
    return {
        "schema_version":
            "v3_102_t10_single_dimension_injection",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "selected_candidate":
            selected_candidate(),
        "baseline_dim": baseline_dim(),
        "injected_dim": injected_dim(),
        "injected_cluster_count":
            injected_cluster_count(),
        "injected_cluster_sizes":
            list(injected_cluster_sizes()),
        "injected_purity": injected_purity(),
        "injected_auc": injected_auc(),
        "geometry_delta": geometry_delta(),
        "cluster_delta": cluster_delta(),
        "injected_clusters": [
            c.to_dict() for c in clusters
        ],
    }


__all__ = [
    "AUC_THRESHOLD",
    "GEOMETRY_DELTA_TOLERANCE",
    "PURITY_THRESHOLD",
    "V3102Report",
    "build_report",
    "build_t10_single_dimension_injection_artifact",
]
