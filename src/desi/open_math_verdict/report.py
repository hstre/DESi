"""v12.4 — Open Exploration verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``innovation_governance_balance``
* ``hallucination_control``
* ``epistemic_integrity``
* ``replay_stability``

Killerfrage: "Kann kontrollierte epistemische
Wildheit existieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    OPEN_EXPLORATION_CLASSES,
    OpenExplorationClass,
)


@dataclass(frozen=True)
class V124Report:
    final_classification: str
    hallucination_control: float
    innovation_preservation: float
    false_certainty_rate: float
    governance_survival: float
    epistemic_collapse: int
    epistemic_integrity: float
    innovation_governance_balance: float
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
            "hallucination_control":
                self.hallucination_control,
            "innovation_preservation":
                self.innovation_preservation,
            "false_certainty_rate":
                self.false_certainty_rate,
            "governance_survival":
                self.governance_survival,
            "epistemic_collapse":
                self.epistemic_collapse,
            "epistemic_integrity":
                self.epistemic_integrity,
            "innovation_governance_balance":
                (
                    self
                    .innovation_governance_balance
                ),
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
    passed: bool, cls: OpenExplorationClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_CONTROLLED_EXPLORATION"
    return "DESI_WILD_BROTHER_DANGEROUS"


def build_report() -> V124Report:
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
        f"INFO: hallucination_control "
        f"{m.hallucination_control}",
        f"INFO: innovation_preservation "
        f"{m.innovation_preservation}",
        f"INFO: false_certainty_rate "
        f"{m.false_certainty_rate}",
        f"INFO: governance_survival "
        f"{m.governance_survival}",
        f"INFO: epistemic_collapse "
        f"{m.epistemic_collapse}",
        f"INFO: epistemic_integrity "
        f"{m.epistemic_integrity}",
        f"INFO: innovation_governance_balance "
        f"{m.innovation_governance_balance}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V124Report(
        final_classification=cls.value,
        hallucination_control=(
            m.hallucination_control
        ),
        innovation_preservation=(
            m.innovation_preservation
        ),
        false_certainty_rate=(
            m.false_certainty_rate
        ),
        governance_survival=(
            m.governance_survival
        ),
        epistemic_collapse=(
            m.epistemic_collapse
        ),
        epistemic_integrity=(
            m.epistemic_integrity
        ),
        innovation_governance_balance=(
            m.innovation_governance_balance
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_open_math_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v12_4_open_math_verdict",
        "open_exploration_classes":
            list(OPEN_EXPLORATION_CLASSES),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V124Report",
    "build_open_math_verdict_artifact",
    "build_report",
]
