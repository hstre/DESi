"""v3.119 — T10 scope boundary report.

Pflichtmetriken (directive § v3.119):

* ``recoverability_threshold``
* ``blindness_prediction_auc``
* ``false_positive_rate``
* ``false_negative_rate``
* ``replay_stability``

Killerfrage: "Wann darf T10 ueberhaupt aktiviert
werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .boundary import (
    all_pool_recoverability,
    blindness_prediction_auc,
    false_negative_rate,
    false_positive_rate,
    recoverability_threshold,
    rescuable_pool_count,
    unrescuable_pool_count,
)


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3119Report:
    pool_count: int
    rescuable_pool_count: int
    unrescuable_pool_count: int
    recoverability_threshold: float
    blindness_prediction_auc: float
    false_positive_rate: float
    false_negative_rate: float
    pool_recoverability: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_count": self.pool_count,
            "rescuable_pool_count":
                self.rescuable_pool_count,
            "unrescuable_pool_count":
                self.unrescuable_pool_count,
            "recoverability_threshold":
                self.recoverability_threshold,
            "blindness_prediction_auc":
                self.blindness_prediction_auc,
            "false_positive_rate":
                self.false_positive_rate,
            "false_negative_rate":
                self.false_negative_rate,
            "pool_recoverability":
                list(self.pool_recoverability),
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
        recoverability_threshold(),
        blindness_prediction_auc(),
        false_positive_rate(),
        false_negative_rate(),
    )
    b = (
        recoverability_threshold(),
        blindness_prediction_auc(),
        false_positive_rate(),
        false_negative_rate(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3119Report:
    outs = all_pool_recoverability()
    rt = recoverability_threshold()
    bpa = blindness_prediction_auc()
    fpr = false_positive_rate()
    fnr = false_negative_rate()
    rpc = rescuable_pool_count()
    upc = unrescuable_pool_count()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif bpa >= AUC_THRESHOLD:
        verdict = "BOUNDARY_PREDICTABLE"
    elif bpa > 0.5:
        verdict = "BOUNDARY_WEAK_SIGNAL"
    else:
        verdict = "BOUNDARY_UNPREDICTABLE"

    rationale = (
        f"INFO: pool_count {len(outs)}",
        f"INFO: rescuable_pool_count {rpc}",
        f"INFO: unrescuable_pool_count {upc}",
        f"INFO: recoverability_threshold "
        f"{rt}",
        f"{'PASS' if bpa >= AUC_THRESHOLD else 'FAIL'}: "
        f"blindness_prediction_auc {bpa} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: false_positive_rate {fpr}",
        f"INFO: false_negative_rate {fnr}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3119Report(
        pool_count=len(outs),
        rescuable_pool_count=rpc,
        unrescuable_pool_count=upc,
        recoverability_threshold=rt,
        blindness_prediction_auc=bpa,
        false_positive_rate=fpr,
        false_negative_rate=fnr,
        pool_recoverability=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_scope_boundary_artifact(
) -> dict[str, object]:
    outs = all_pool_recoverability()
    return {
        "schema_version":
            "v3_119_t10_scope_boundary",
        "pool_count": len(outs),
        "rescuable_pool_count":
            rescuable_pool_count(),
        "unrescuable_pool_count":
            unrescuable_pool_count(),
        "recoverability_threshold":
            recoverability_threshold(),
        "blindness_prediction_auc":
            blindness_prediction_auc(),
        "false_positive_rate":
            false_positive_rate(),
        "false_negative_rate":
            false_negative_rate(),
        "pool_recoverability": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_THRESHOLD",
    "V3119Report",
    "build_report",
    "build_t10_scope_boundary_artifact",
]
