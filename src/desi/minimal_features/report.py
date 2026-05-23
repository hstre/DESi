"""v3.82 — minimal feature detection report.

Pflichtmetriken (directive § v3.82):

* ``feature_importance``
* ``minimal_cluster_accuracy``
* ``proxy_score``
* ``replay_stability``
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..doppelgaenger.report import (
    PURITY_THRESHOLD,
)
from ..redundancy_masking.equivalence import (
    PROBE_RADIUS,
)
from .ablation import (
    all_ablation_outcomes,
)
from .importance import (
    baseline_purity, feature_importance,
    minimal_cluster_accuracy,
    minimal_feature_set, proxy_score,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V382Report:
    probe_radius: float
    baseline_purity: float
    ablation_outcomes: tuple[dict, ...]
    feature_importance: tuple[dict, ...]
    minimal_feature_set: tuple[str, ...]
    minimal_feature_count: int
    minimal_cluster_accuracy: float
    proxy_score: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "baseline_purity": self.baseline_purity,
            "ablation_outcomes":
                list(self.ablation_outcomes),
            "feature_importance":
                list(self.feature_importance),
            "minimal_feature_set":
                list(self.minimal_feature_set),
            "minimal_feature_count":
                self.minimal_feature_count,
            "minimal_cluster_accuracy":
                self.minimal_cluster_accuracy,
            "proxy_score": self.proxy_score,
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
        o.to_dict()
        for o in all_ablation_outcomes()
    ]
    b = [
        o.to_dict()
        for o in all_ablation_outcomes()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V382Report:
    base = baseline_purity()
    outcomes = all_ablation_outcomes()
    imps = feature_importance()
    minimal = minimal_feature_set()
    mca = minimal_cluster_accuracy()
    ps = proxy_score()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        mca >= PURITY_THRESHOLD
        and len(minimal) <= 3
    ):
        verdict = "MINIMAL_PROXY_FOUND"
    elif mca >= PURITY_THRESHOLD:
        verdict = "PROXY_FOUND_NOT_MINIMAL"
    else:
        verdict = "NO_MINIMAL_PROXY"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: baseline_purity {base}",
        f"INFO: ablation_outcomes "
        f"{[o.to_dict() for o in outcomes]}",
        f"INFO: feature_importance "
        f"{[f.to_dict() for f in imps]}",
        f"INFO: minimal_feature_set "
        f"{list(minimal)} (count "
        f"{len(minimal)})",
        f"{'PASS' if mca >= PURITY_THRESHOLD else 'FAIL'}: "
        f"minimal_cluster_accuracy {mca} "
        f"(threshold {PURITY_THRESHOLD})",
        f"INFO: proxy_score {ps}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V382Report(
        probe_radius=PROBE_RADIUS,
        baseline_purity=base,
        ablation_outcomes=tuple(
            o.to_dict() for o in outcomes
        ),
        feature_importance=tuple(
            f.to_dict() for f in imps
        ),
        minimal_feature_set=minimal,
        minimal_feature_count=len(minimal),
        minimal_cluster_accuracy=mca,
        proxy_score=ps,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_minimal_feature_detection_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_82_minimal_feature_detection",
        "probe_radius": PROBE_RADIUS,
        "baseline_purity": baseline_purity(),
        "ablation_outcomes": [
            o.to_dict()
            for o in all_ablation_outcomes()
        ],
        "feature_importance": [
            f.to_dict()
            for f in feature_importance()
        ],
        "minimal_feature_set":
            list(minimal_feature_set()),
        "minimal_cluster_accuracy":
            minimal_cluster_accuracy(),
        "proxy_score": proxy_score(),
    }


__all__ = [
    "V382Report",
    "build_minimal_feature_detection_artifact",
    "build_report",
]
