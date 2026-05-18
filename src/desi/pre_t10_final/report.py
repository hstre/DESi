"""v3.120d — final pre-T10 rule report.

Pflichtmetriken (directive § v3.120d):

* ``final_far``
* ``final_tpr``
* ``rule_roi``
* ``historical_gate_flip_count``
* ``replay_stability``

Killerfrage: "Darf Pre-T10 jetzt offiziell vor
jede Expansion?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decision import (
    gate_failing_conditions,
    gate_passes_all,
)
from .rule import (
    calibration_window_exists,
    final_adverse_flips,
    final_far,
    final_false_negative_rate,
    final_historical_gate_flip_count,
    final_rule_roi,
    final_threshold,
    final_threshold_drift,
    final_tpr,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3120dReport:
    final_threshold: float
    final_far: float
    final_tpr: float
    threshold_drift: float
    adverse_flips: int
    false_negative_rate: float
    rule_roi: float
    historical_gate_flip_count: int
    calibration_window_exists: bool
    gate_passes_all: bool
    failing_conditions: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "final_threshold":
                self.final_threshold,
            "final_far": self.final_far,
            "final_tpr": self.final_tpr,
            "threshold_drift":
                self.threshold_drift,
            "adverse_flips":
                self.adverse_flips,
            "false_negative_rate":
                self.false_negative_rate,
            "rule_roi": self.rule_roi,
            "historical_gate_flip_count":
                self
                .historical_gate_flip_count,
            "calibration_window_exists":
                self.calibration_window_exists,
            "gate_passes_all":
                self.gate_passes_all,
            "failing_conditions":
                list(self.failing_conditions),
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
        final_far(),
        final_tpr(),
        final_threshold_drift(),
        gate_passes_all(),
    )
    b = (
        final_far(),
        final_tpr(),
        final_threshold_drift(),
        gate_passes_all(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3120dReport:
    passed = gate_passes_all()
    failing = gate_failing_conditions()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif passed:
        verdict = "PRE_T10_ACTIVATED"
    else:
        verdict = "PRE_T10_EXPERIMENTAL"

    rationale = (
        f"INFO: final_threshold "
        f"{final_threshold()}",
        f"INFO: final_far {final_far()}",
        f"INFO: final_tpr {final_tpr()}",
        f"INFO: threshold_drift "
        f"{final_threshold_drift()}",
        f"INFO: adverse_flips "
        f"{final_adverse_flips()}",
        f"INFO: false_negative_rate "
        f"{final_false_negative_rate()}",
        f"INFO: rule_roi {final_rule_roi()}",
        f"INFO: historical_gate_flip_count "
        f"{final_historical_gate_flip_count()}",
        f"INFO: calibration_window_exists "
        f"{calibration_window_exists()}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3120dReport(
        final_threshold=final_threshold(),
        final_far=final_far(),
        final_tpr=final_tpr(),
        threshold_drift=(
            final_threshold_drift()
        ),
        adverse_flips=final_adverse_flips(),
        false_negative_rate=(
            final_false_negative_rate()
        ),
        rule_roi=final_rule_roi(),
        historical_gate_flip_count=(
            final_historical_gate_flip_count()
        ),
        calibration_window_exists=(
            calibration_window_exists()
        ),
        gate_passes_all=passed,
        failing_conditions=failing,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_final_rule_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_120d_pre_t10_final_rule",
        "final_threshold": final_threshold(),
        "final_far": final_far(),
        "final_tpr": final_tpr(),
        "threshold_drift":
            final_threshold_drift(),
        "adverse_flips":
            final_adverse_flips(),
        "false_negative_rate":
            final_false_negative_rate(),
        "rule_roi": final_rule_roi(),
        "historical_gate_flip_count":
            final_historical_gate_flip_count(),
        "calibration_window_exists":
            calibration_window_exists(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V3120dReport",
    "build_pre_t10_final_rule_artifact",
    "build_report",
]
