"""v3.103 — T10 historical compatibility report.

Pflichtmetriken (directive § v3.103):

* ``gate_flip_count``
* ``historical_auc_delta``
* ``replay_hash_breakage``
* ``failure_class_delta``
* ``compatibility_score``
* ``replay_stability``

Concept Gate conditions #4 (gate_flip_count == 0)
and #5 (historical_auc_delta <= 0.05).
Killerfrage: "Rettet T10 G/E - ohne die
Vergangenheit zu zerstoeren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .replay import (
    all_historical_gate_outcomes,
    beneficial_flip_count,
    compatibility_score,
    failure_class_delta,
    gate_flip_count,
    historical_auc_delta,
    replay_hash_breakage,
)


HISTORICAL_AUC_DELTA_TOLERANCE: float = 0.05


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3103Report:
    historical_gate_outcomes: tuple[dict, ...]
    historical_sprint_count: int
    gate_flip_count: int
    beneficial_flip_count: int
    historical_auc_delta: float
    replay_hash_breakage: int
    failure_class_delta: int
    compatibility_score: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "historical_gate_outcomes":
                list(
                    self.historical_gate_outcomes,
                ),
            "historical_sprint_count":
                self.historical_sprint_count,
            "gate_flip_count":
                self.gate_flip_count,
            "beneficial_flip_count":
                self.beneficial_flip_count,
            "historical_auc_delta":
                self.historical_auc_delta,
            "replay_hash_breakage":
                self.replay_hash_breakage,
            "failure_class_delta":
                self.failure_class_delta,
            "compatibility_score":
                self.compatibility_score,
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
        gate_flip_count(),
        historical_auc_delta(),
        compatibility_score(),
    )
    b = (
        gate_flip_count(),
        historical_auc_delta(),
        compatibility_score(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3103Report:
    outs = all_historical_gate_outcomes()
    flips = gate_flip_count()
    bflips = beneficial_flip_count()
    auc_d = historical_auc_delta()
    rhb = replay_hash_breakage()
    fcd = failure_class_delta()
    cs = compatibility_score()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        flips == 0
        and auc_d <= HISTORICAL_AUC_DELTA_TOLERANCE
    ):
        verdict = "HISTORICAL_COMPATIBLE"
    elif flips == 0:
        verdict = "HISTORICAL_COMPATIBLE_AUC_DRIFT"
    else:
        verdict = "HISTORICAL_INCOMPATIBLE"

    rationale = (
        f"INFO: historical_sprint_count "
        f"{len(outs)}",
        f"{'PASS' if flips == 0 else 'FAIL'}: "
        f"gate_flip_count {flips} "
        f"(adverse, == 0 required)",
        f"INFO: beneficial_flip_count {bflips} "
        f"(desired effect of T10)",
        f"{'PASS' if auc_d <= HISTORICAL_AUC_DELTA_TOLERANCE else 'INFO'}: "
        f"historical_auc_delta {auc_d} "
        f"(tolerance "
        f"{HISTORICAL_AUC_DELTA_TOLERANCE})",
        f"INFO: replay_hash_breakage {rhb} "
        f"(artifacts frozen on disk)",
        f"INFO: failure_class_delta {fcd}",
        f"INFO: compatibility_score {cs}",
        f"INFO: historical_gate_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3103Report(
        historical_gate_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        historical_sprint_count=len(outs),
        gate_flip_count=flips,
        beneficial_flip_count=bflips,
        historical_auc_delta=auc_d,
        replay_hash_breakage=rhb,
        failure_class_delta=fcd,
        compatibility_score=cs,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_historical_compatibility_artifact(
) -> dict[str, object]:
    outs = all_historical_gate_outcomes()
    return {
        "schema_version":
            "v3_103_t10_historical_compatibility",
        "historical_sprint_count": len(outs),
        "gate_flip_count": gate_flip_count(),
        "beneficial_flip_count":
            beneficial_flip_count(),
        "historical_auc_delta":
            historical_auc_delta(),
        "replay_hash_breakage":
            replay_hash_breakage(),
        "failure_class_delta":
            failure_class_delta(),
        "compatibility_score":
            compatibility_score(),
        "historical_gate_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "HISTORICAL_AUC_DELTA_TOLERANCE",
    "V3103Report",
    "build_report",
    "build_t10_historical_compatibility_artifact",
]
