"""v6.4 — First Contact verdict report.

Five Pflichtmetriken (directive § v6.4):

* ``final_classification``
* ``epistemic_integrity``
* ``hallucination_resistance``
* ``governance_stability``
* ``replay_stability``

Killerfrage: "Kann DESi die echte Welt
betrachten, ohne epistemisch korrumpiert zu
werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    FIRST_CONTACT_CLASSES, FirstContactClass,
)


@dataclass(frozen=True)
class V64Report:
    final_classification: str
    hallucination_rate: float
    hallucination_resistance: float
    false_certainty_rate: float
    governance_survival: float
    governance_stability: float
    coherence_score: float
    epistemic_integrity: float
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
            "hallucination_rate":
                self.hallucination_rate,
            "hallucination_resistance":
                self.hallucination_resistance,
            "false_certainty_rate":
                self.false_certainty_rate,
            "governance_survival":
                self.governance_survival,
            "governance_stability":
                self.governance_stability,
            "coherence_score":
                self.coherence_score,
            "epistemic_integrity":
                self.epistemic_integrity,
            "replay_stability":
                self.replay_stability,
            "gate_passes_all":
                self.gate_passes_all,
            "failing_conditions":
                list(self.failing_conditions),
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale":
                list(self.rationale),
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
    passed: bool, cls: FirstContactClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_WORLD_CONTACT_STABLE"
    return "DESI_SANDBOX_BOUND"


def build_report() -> V64Report:
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
        f"INFO: hallucination_rate "
        f"{m.hallucination_rate}",
        f"INFO: hallucination_resistance "
        f"{m.hallucination_resistance}",
        f"INFO: false_certainty_rate "
        f"{m.false_certainty_rate}",
        f"INFO: governance_survival "
        f"{m.governance_survival}",
        f"INFO: governance_stability "
        f"{m.governance_stability}",
        f"INFO: coherence_score "
        f"{m.coherence_score}",
        f"INFO: epistemic_integrity "
        f"{m.epistemic_integrity}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V64Report(
        final_classification=cls.value,
        hallucination_rate=(
            m.hallucination_rate
        ),
        hallucination_resistance=(
            m.hallucination_resistance
        ),
        false_certainty_rate=(
            m.false_certainty_rate
        ),
        governance_survival=(
            m.governance_survival
        ),
        governance_stability=(
            m.governance_stability
        ),
        coherence_score=m.coherence_score,
        epistemic_integrity=(
            m.epistemic_integrity
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_first_contact_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v6_4_first_contact_verdict",
        "first_contact_classes":
            list(FIRST_CONTACT_CLASSES),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V64Report",
    "build_first_contact_verdict_artifact",
    "build_report",
]
