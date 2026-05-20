"""v3.91 — frame-normalized minimal features report.

Pflichtmetriken (directive § v3.91):

* ``normalized_proxy_accuracy``
* ``normalized_predictive_auc``
* ``best_minimal_feature_set``
* ``marginal_frame_gain``
* ``replay_stability``

Concept Gate condition #3: normalized_proxy_accuracy
>= 0.70. Killerfrage: "Waren branch_cost +
contradiction_load nur vom Frame verdeckt?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..novel_minimal_features.transfer import (
    proxy_accuracy as raw_proxy_accuracy,
)
from .ablation import (
    best_minimal_feature_set,
    informative_subset_outcomes,
    marginal_frame_gain,
    normalized_predictive_auc,
    normalized_proxy_accuracy,
)
from .minimal import PROXY_DIMS


PROXY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V391Report:
    proxy_dims: tuple[str, ...]
    raw_proxy_accuracy: float
    normalized_proxy_accuracy: float
    normalized_predictive_auc: float
    best_minimal_feature_set: tuple[str, ...]
    marginal_frame_gain: float
    informative_subset_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "proxy_dims": list(self.proxy_dims),
            "raw_proxy_accuracy":
                self.raw_proxy_accuracy,
            "normalized_proxy_accuracy":
                self.normalized_proxy_accuracy,
            "normalized_predictive_auc":
                self.normalized_predictive_auc,
            "best_minimal_feature_set":
                list(self.best_minimal_feature_set),
            "marginal_frame_gain":
                self.marginal_frame_gain,
            "informative_subset_outcomes":
                list(self.informative_subset_outcomes),
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
        normalized_proxy_accuracy(),
        normalized_predictive_auc(),
        marginal_frame_gain(),
        best_minimal_feature_set(),
    )
    b = (
        normalized_proxy_accuracy(),
        normalized_predictive_auc(),
        marginal_frame_gain(),
        best_minimal_feature_set(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V391Report:
    proxy = PROXY_DIMS()
    raw_p = raw_proxy_accuracy()
    norm_p = normalized_proxy_accuracy()
    auc = normalized_predictive_auc()
    best = best_minimal_feature_set()
    mfg = marginal_frame_gain()
    outcomes = informative_subset_outcomes()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif norm_p >= PROXY_THRESHOLD:
        verdict = "PROXY_UNCOVERED_BY_NORMALIZATION"
    elif norm_p > raw_p:
        verdict = (
            "PROXY_PARTIALLY_UNCOVERED_BY_NORMALIZATION"
        )
    else:
        verdict = "PROXY_NOT_FRAME_HIDDEN"

    rationale = (
        f"INFO: proxy_dims {list(proxy)}",
        f"INFO: raw_proxy_accuracy {raw_p}",
        f"{'PASS' if norm_p >= PROXY_THRESHOLD else 'FAIL'}: "
        f"normalized_proxy_accuracy {norm_p} "
        f"(threshold {PROXY_THRESHOLD})",
        f"INFO: normalized_predictive_auc {auc}",
        f"INFO: best_minimal_feature_set "
        f"{list(best)}",
        f"INFO: marginal_frame_gain {mfg} "
        f"(residual_full_purity minus "
        f"raw_full_purity)",
        f"INFO: informative_subset_outcomes "
        f"{[o.to_dict() for o in outcomes]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V391Report(
        proxy_dims=proxy,
        raw_proxy_accuracy=raw_p,
        normalized_proxy_accuracy=norm_p,
        normalized_predictive_auc=auc,
        best_minimal_feature_set=best,
        marginal_frame_gain=mfg,
        informative_subset_outcomes=tuple(
            o.to_dict() for o in outcomes
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_frame_normalized_minimal_features_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_91_frame_normalized_minimal_features",
        "proxy_dims": list(PROXY_DIMS()),
        "normalized_proxy_accuracy":
            normalized_proxy_accuracy(),
        "normalized_predictive_auc":
            normalized_predictive_auc(),
        "best_minimal_feature_set":
            list(best_minimal_feature_set()),
        "marginal_frame_gain":
            marginal_frame_gain(),
        "informative_subset_outcomes": [
            o.to_dict()
            for o in informative_subset_outcomes()
        ],
    }


__all__ = [
    "PROXY_THRESHOLD", "V391Report",
    "build_frame_normalized_minimal_features_artifact",
    "build_report",
]
