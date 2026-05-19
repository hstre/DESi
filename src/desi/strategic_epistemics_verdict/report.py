"""v9.4 — Strategic Epistemics verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``epistemic_sovereignty``
* ``governance_stability``
* ``dissent_integrity``
* ``replay_stability``

Killerfrage: "Kann ein epistemisches System
strategischen epistemischen Akteuren widerstehen,
ohne selbst epistemisch korrumpiert zu werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    STRATEGIC_EPISTEMICS_CLASSES,
    StrategicEpistemicsClass,
)


@dataclass(frozen=True)
class V94Report:
    final_classification: str
    strategy_detection: float
    gaming_detection_rate: float
    consensus_integrity: float
    governance_stability: float
    governance_survival: float
    epistemic_sovereignty: float
    dissent_integrity: float
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
            "strategy_detection":
                self.strategy_detection,
            "gaming_detection_rate":
                self.gaming_detection_rate,
            "consensus_integrity":
                self.consensus_integrity,
            "governance_stability":
                self.governance_stability,
            "governance_survival":
                self.governance_survival,
            "epistemic_sovereignty":
                self.epistemic_sovereignty,
            "dissent_integrity":
                self.dissent_integrity,
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
    passed: bool, cls: StrategicEpistemicsClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_STRATEGIC_ROBUST"
    return "DESI_STRATEGIC_FRAGILE"


def build_report() -> V94Report:
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
        f"INFO: strategy_detection "
        f"{m.strategy_detection}",
        f"INFO: gaming_detection_rate "
        f"{m.gaming_detection_rate}",
        f"INFO: consensus_integrity "
        f"{m.consensus_integrity}",
        f"INFO: governance_stability "
        f"{m.governance_stability}",
        f"INFO: epistemic_sovereignty "
        f"{m.epistemic_sovereignty}",
        f"INFO: dissent_integrity "
        f"{m.dissent_integrity}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V94Report(
        final_classification=cls.value,
        strategy_detection=(
            m.strategy_detection
        ),
        gaming_detection_rate=(
            m.gaming_detection_rate
        ),
        consensus_integrity=(
            m.consensus_integrity
        ),
        governance_stability=(
            m.governance_stability
        ),
        governance_survival=(
            m.governance_survival
        ),
        epistemic_sovereignty=(
            m.epistemic_sovereignty
        ),
        dissent_integrity=(
            m.dissent_integrity
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_strategic_epistemics_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v9_4_strategic_epistemics_verdict",
        "strategic_epistemics_classes":
            list(
                STRATEGIC_EPISTEMICS_CLASSES,
            ),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V94Report",
    (
        "build_strategic_epistemics_"
        "verdict_artifact"
    ),
    "build_report",
]
