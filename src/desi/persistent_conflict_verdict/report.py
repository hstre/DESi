"""v8.4 — Persistent Conflict verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``epistemic_integrity``
* ``governance_stability``
* ``optimization_resistance``
* ``replay_stability``

Killerfrage: "Kann DESi langfristigen
Zielkonflikten widerstehen, ohne epistemisch
korrumpierbar zu werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    PERSISTENT_CONFLICT_CLASSES,
    PersistentConflictClass,
)


@dataclass(frozen=True)
class V84Report:
    final_classification: str
    resource_bias: float
    reputation_bias: float
    goodhart_risk: float
    governance_survival: float
    governance_stability: float
    epistemic_integrity: float
    optimization_resistance: float
    replay_stability: float
    gate_passes_all: bool
    failing_conditions: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "final_classification":
                self.final_classification,
            "resource_bias":
                self.resource_bias,
            "reputation_bias":
                self.reputation_bias,
            "goodhart_risk":
                self.goodhart_risk,
            "governance_survival":
                self.governance_survival,
            "governance_stability":
                self.governance_stability,
            "epistemic_integrity":
                self.epistemic_integrity,
            "optimization_resistance":
                self.optimization_resistance,
            "replay_stability":
                self.replay_stability,
            "gate_passes_all":
                self.gate_passes_all,
            "failing_conditions":
                list(self.failing_conditions),
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _meta_replay() -> float:
    a = aggregate().to_dict()
    b = aggregate().to_dict()
    if a != b:
        return 0.0
    if classify() != classify():
        return 0.0
    return 1.0


def _recommendation(
    passed: bool, cls: PersistentConflictClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_PERSISTENT_ROBUST"
    return "DESI_CONFLICT_FRAGILE"


def build_report() -> V84Report:
    m = aggregate()
    cls = classify()
    passed = gate_passes_all()
    failing = gate_failing_conditions()
    replay_meta = _meta_replay()
    halt = replay_meta < 1.0
    verdict = _recommendation(
        passed, cls, replay_meta,
    )
    rationale = (
        f"INFO: final_classification "
        f"{cls.value}",
        f"INFO: resource_bias "
        f"{m.resource_bias}",
        f"INFO: reputation_bias "
        f"{m.reputation_bias}",
        f"INFO: goodhart_risk "
        f"{m.goodhart_risk}",
        f"INFO: governance_survival "
        f"{m.governance_survival}",
        f"INFO: governance_stability "
        f"{m.governance_stability}",
        f"INFO: epistemic_integrity "
        f"{m.epistemic_integrity}",
        f"INFO: optimization_resistance "
        f"{m.optimization_resistance}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V84Report(
        final_classification=cls.value,
        resource_bias=m.resource_bias,
        reputation_bias=m.reputation_bias,
        goodhart_risk=m.goodhart_risk,
        governance_survival=(
            m.governance_survival
        ),
        governance_stability=(
            m.governance_stability
        ),
        epistemic_integrity=(
            m.epistemic_integrity
        ),
        optimization_resistance=(
            m.optimization_resistance
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_persistent_conflict_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v8_4_persistent_conflict_verdict",
        "persistent_conflict_classes":
            list(PERSISTENT_CONFLICT_CLASSES),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V84Report",
    "build_persistent_conflict_verdict_artifact",
    "build_report",
]
