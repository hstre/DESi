"""v3.87 — minimal feature transfer report.

Pflichtmetriken (directive § v3.87):

* ``proxy_accuracy``
* ``proxy_gap``
* ``new_informative_dims``
* ``feature_stability``
* ``replay_stability``

Concept gate (§ v3.87): ``proxy_accuracy >= 0.70``
(condition #4 of the sprint Concept Gate). Killer
frage: "Sind branch_cost + contradiction_load
universell?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .minimal import (
    PROXY_DIMS, cluster_with_full,
    cluster_with_proxy,
)
from .transfer import (
    DimContribution, baseline_full_purity,
    feature_stability, new_informative_dims,
    proxy_accuracy, proxy_gap,
)


PROXY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V387Report:
    proxy_dims: tuple[str, ...]
    proxy_accuracy: float
    baseline_full_purity: float
    proxy_gap: float
    new_informative_dims: tuple[dict, ...]
    feature_stability: float
    proxy_cluster_count: int
    proxy_cluster_sizes: tuple[int, ...]
    full_cluster_count: int
    full_cluster_sizes: tuple[int, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "proxy_dims": list(self.proxy_dims),
            "proxy_accuracy": self.proxy_accuracy,
            "baseline_full_purity":
                self.baseline_full_purity,
            "proxy_gap": self.proxy_gap,
            "new_informative_dims":
                list(self.new_informative_dims),
            "feature_stability":
                self.feature_stability,
            "proxy_cluster_count":
                self.proxy_cluster_count,
            "proxy_cluster_sizes":
                list(self.proxy_cluster_sizes),
            "full_cluster_count":
                self.full_cluster_count,
            "full_cluster_sizes":
                list(self.full_cluster_sizes),
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
        proxy_accuracy(),
        baseline_full_purity(),
        proxy_gap(),
        feature_stability(),
    )
    b = (
        proxy_accuracy(),
        baseline_full_purity(),
        proxy_gap(),
        feature_stability(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V387Report:
    proxy_dims = PROXY_DIMS()
    proxy_p = proxy_accuracy()
    full_p = baseline_full_purity()
    gap = proxy_gap()
    new_dims = new_informative_dims()
    stab = feature_stability()
    proxy_cls = cluster_with_proxy()
    full_cls = cluster_with_full()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif proxy_p >= PROXY_THRESHOLD:
        verdict = "PROXY_TRANSFERS"
    elif gap <= 0.0:
        verdict = "PROXY_PARTIAL_TRANSFER"
    else:
        verdict = "PROXY_DOES_NOT_TRANSFER"

    rationale = (
        f"INFO: proxy_dims {list(proxy_dims)}",
        f"INFO: baseline_full_purity {full_p}",
        f"{'PASS' if proxy_p >= PROXY_THRESHOLD else 'FAIL'}: "
        f"proxy_accuracy {proxy_p} "
        f"(threshold {PROXY_THRESHOLD})",
        f"INFO: proxy_gap {gap} "
        f"(negative ⇒ proxy beats full)",
        f"INFO: new_informative_dims "
        f"{[d.to_dict() for d in new_dims]}",
        f"INFO: feature_stability {stab} "
        f"(novel proxy purity / plateau proxy "
        f"purity)",
        f"INFO: proxy_cluster_count "
        f"{len(proxy_cls)} sizes "
        f"{tuple(len(c.members) for c in proxy_cls)}",
        f"INFO: full_cluster_count "
        f"{len(full_cls)} sizes "
        f"{tuple(len(c.members) for c in full_cls)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V387Report(
        proxy_dims=proxy_dims,
        proxy_accuracy=proxy_p,
        baseline_full_purity=full_p,
        proxy_gap=gap,
        new_informative_dims=tuple(
            d.to_dict() for d in new_dims
        ),
        feature_stability=stab,
        proxy_cluster_count=len(proxy_cls),
        proxy_cluster_sizes=tuple(
            len(c.members) for c in proxy_cls
        ),
        full_cluster_count=len(full_cls),
        full_cluster_sizes=tuple(
            len(c.members) for c in full_cls
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_novel_family_proxy_artifact(
) -> dict[str, object]:
    proxy_cls = cluster_with_proxy()
    full_cls = cluster_with_full()
    return {
        "schema_version":
            "v3_87_novel_family_proxy",
        "proxy_dims": list(PROXY_DIMS()),
        "proxy_accuracy": proxy_accuracy(),
        "baseline_full_purity":
            baseline_full_purity(),
        "proxy_gap": proxy_gap(),
        "feature_stability": feature_stability(),
        "new_informative_dims": [
            d.to_dict()
            for d in new_informative_dims()
        ],
        "proxy_clusters": [
            c.to_dict() for c in proxy_cls
        ],
        "full_clusters": [
            c.to_dict() for c in full_cls
        ],
    }


__all__ = [
    "PROXY_THRESHOLD", "V387Report",
    "build_novel_family_proxy_artifact",
    "build_report",
]
