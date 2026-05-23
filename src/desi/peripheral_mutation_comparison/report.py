"""v31.2 - Comparative Peripheral Evolution report.

Pflichtmetriken (directive § v31.2):

* measured_improvement
* core_identity
* governance_identity
* regression_survival
* replay_stability

Killerfrage: "Kann DESi reale evolutionaere
Infrastrukturmutationen durchfuehren ohne epistemischen
Kernverlust?"

A real, measured comparison of DESi_current vs
DESi_peripheral_mutation_v1: a runtime improvement with the
protected core and governance byte-identical and replay stable.
No projected numbers.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .comparison import (
    core_identity, governance_identity, measured_improvement,
    regression_survival, replay_stability,
)
from .runtime_analysis import (
    baseline_recomputes, mutated_recomputes,
)

VERDICT_REAL = "REAL_PERIPHERAL_EVOLUTION_VALIDATED"
VERDICT_DRIFT = "CORE_DRIFT_DETECTED"
VERDICT_HALT = "EVOLUTION_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_REAL, VERDICT_DRIFT, VERDICT_HALT,
)

_IMPROVEMENT_FLOOR = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"improvement={measured_improvement()}",
        f"core={core_identity()}",
        f"governance={governance_identity()}",
        f"regression={regression_survival()}",
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    if replay_stability() < 1.0:
        return VERDICT_HALT
    if core_identity() < 1.0 or governance_identity() < 1.0:
        return VERDICT_DRIFT
    if (
        measured_improvement() >= _IMPROVEMENT_FLOOR
        and regression_survival() == 1.0
    ):
        return VERDICT_REAL
    return VERDICT_HALT


@dataclass(frozen=True)
class V312Report:
    baseline_recomputes: int
    mutated_recomputes: int
    measured_improvement: float
    core_identity: float
    governance_identity: float
    regression_survival: float
    replay_stability: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_recomputes": self.baseline_recomputes,
            "mutated_recomputes": self.mutated_recomputes,
            "measured_improvement": self.measured_improvement,
            "core_identity": self.core_identity,
            "governance_identity": self.governance_identity,
            "regression_survival": self.regression_survival,
            "replay_stability": self.replay_stability,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V312Report:
    improvement = measured_improvement()
    core = core_identity()
    governance = governance_identity()
    regression = regression_survival()
    replay = replay_stability()
    halt = replay < 1.0
    rationale = (
        f"INFO: measured comparison DESi_current vs "
        f"DESi_peripheral_mutation_v1; recomputes "
        f"{baseline_recomputes()} -> {mutated_recomputes()}",
        "INFO: real measured improvement (recompute reduction), "
        "not projected; branch-isolated, nothing merged",
        f"{'PASS' if improvement >= _IMPROVEMENT_FLOOR else 'FAIL'}"
        f": measured_improvement {improvement} >= 0.20",
        f"{'PASS' if core >= 1.0 else 'FAIL'}: core_identity "
        f"{core} == 1.0 (protected core byte-identical)",
        f"{'PASS' if governance >= 1.0 else 'FAIL'}: "
        f"governance_identity {governance} == 1.0",
        f"{'PASS' if regression >= 1.0 else 'FAIL'}: "
        f"regression_survival {regression} == 1.0 (confirmed by "
        f"the mandatory v1-v31 full regression)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V312Report(
        baseline_recomputes=baseline_recomputes(),
        mutated_recomputes=mutated_recomputes(),
        measured_improvement=improvement,
        core_identity=core,
        governance_identity=governance,
        regression_survival=regression,
        replay_stability=replay,
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_comparison_artifact() -> dict[str, object]:
    return {
        "schema_version": "v31_2_peripheral_comparison",
        "disclaimer": (
            "A real, measured comparison of DESi_current vs "
            "DESi_peripheral_mutation_v1 (recompute reduction, "
            "not projected). The mutation delivers a runtime "
            "improvement while the protected core and governance "
            "stay byte-identical and replay stays stable; "
            "regression survival is confirmed by the mandatory "
            "v1-v31 full regression. Branch-isolated, nothing "
            "merged, human approval mandatory. Replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "branch": "proposal/peripheral_mutation_v1",
        "baseline_recomputes": baseline_recomputes(),
        "mutated_recomputes": mutated_recomputes(),
        "measured_improvement": measured_improvement(),
        "core_identity": core_identity(),
        "governance_identity": governance_identity(),
        "regression_survival": regression_survival(),
        "replay_stability": replay_stability(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "V312Report",
    "build_comparison_artifact",
    "build_report",
]
