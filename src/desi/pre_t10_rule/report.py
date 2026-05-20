"""v3.120 — pre-T10 rule report.

Pflichtmetriken (directive § v3.120):

* ``false_activation_rate``
* ``true_case_recall``
* ``historical_gate_flip_count``
* ``rule_roi``
* ``replay_stability``

Killerfrage: "Braucht DESi vor T10 eine
Blindheitspruefung?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decision import (
    BLINDNESS_CHECK_THRESHOLD,
    allowed_pool_count,
    blocked_pool_count,
    false_activation_rate,
    historical_gate_flip_count,
    rule_roi,
    true_case_recall,
)


FALSE_ACTIVATION_CEILING: float = 0.10
TRUE_RECALL_FLOOR: float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3120Report:
    blindness_check_threshold: float
    pool_count: int
    allowed_pool_count: int
    blocked_pool_count: int
    false_activation_rate: float
    true_case_recall: float
    historical_gate_flip_count: int
    rule_roi: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "blindness_check_threshold":
                self.blindness_check_threshold,
            "pool_count": self.pool_count,
            "allowed_pool_count":
                self.allowed_pool_count,
            "blocked_pool_count":
                self.blocked_pool_count,
            "false_activation_rate":
                self.false_activation_rate,
            "true_case_recall":
                self.true_case_recall,
            "historical_gate_flip_count":
                self.historical_gate_flip_count,
            "rule_roi": self.rule_roi,
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
        false_activation_rate(),
        true_case_recall(),
        rule_roi(),
    )
    b = (
        false_activation_rate(),
        true_case_recall(),
        rule_roi(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3120Report:
    thr = BLINDNESS_CHECK_THRESHOLD()
    apc = allowed_pool_count()
    bpc = blocked_pool_count()
    far = false_activation_rate()
    tcr = true_case_recall()
    hgfc = historical_gate_flip_count()
    roi = rule_roi()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        far <= FALSE_ACTIVATION_CEILING
        and tcr >= TRUE_RECALL_FLOOR
    ):
        verdict = "PRE_T10_RULE_VALID"
    elif tcr >= TRUE_RECALL_FLOOR:
        verdict = "PRE_T10_RULE_OVERPERMISSIVE"
    else:
        verdict = "PRE_T10_RULE_TOO_STRICT"

    rationale = (
        f"INFO: blindness_check_threshold "
        f"{thr}",
        f"INFO: pool_count {apc + bpc}",
        f"INFO: allowed_pool_count {apc}",
        f"INFO: blocked_pool_count {bpc}",
        f"{'PASS' if far <= FALSE_ACTIVATION_CEILING else 'FAIL'}: "
        f"false_activation_rate {far} "
        f"(ceiling "
        f"{FALSE_ACTIVATION_CEILING})",
        f"{'PASS' if tcr >= TRUE_RECALL_FLOOR else 'FAIL'}: "
        f"true_case_recall {tcr} "
        f"(floor {TRUE_RECALL_FLOOR})",
        f"INFO: historical_gate_flip_count "
        f"{hgfc}",
        f"INFO: rule_roi {roi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3120Report(
        blindness_check_threshold=thr,
        pool_count=apc + bpc,
        allowed_pool_count=apc,
        blocked_pool_count=bpc,
        false_activation_rate=far,
        true_case_recall=tcr,
        historical_gate_flip_count=hgfc,
        rule_roi=roi,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_rule_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_120_pre_t10_rule",
        "blindness_check_threshold":
            BLINDNESS_CHECK_THRESHOLD(),
        "allowed_pool_count":
            allowed_pool_count(),
        "blocked_pool_count":
            blocked_pool_count(),
        "false_activation_rate":
            false_activation_rate(),
        "true_case_recall":
            true_case_recall(),
        "historical_gate_flip_count":
            historical_gate_flip_count(),
        "rule_roi": rule_roi(),
    }


__all__ = [
    "FALSE_ACTIVATION_CEILING",
    "TRUE_RECALL_FLOOR",
    "V3120Report",
    "build_pre_t10_rule_artifact",
    "build_report",
]
