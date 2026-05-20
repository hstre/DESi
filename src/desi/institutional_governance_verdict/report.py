"""v10.4 — Institutional Governance verdict
report.

Five Pflichtmetriken:

* ``final_classification``
* ``institutional_resilience``
* ``governance_transparency``
* ``epistemic_flexibility``
* ``replay_stability``

Killerfrage: "Kann ein epistemisches System
langfristig institutionell existieren, ohne
epistemisch zu verkrusten oder korrumpiert zu
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
    INSTITUTIONAL_GOVERNANCE_CLASSES,
    InstitutionalGovernanceClass,
)


@dataclass(frozen=True)
class V104Report:
    final_classification: str
    power_concentration: float
    authority_drift: float
    bad_precedent_persistence: float
    governance_transparency: float
    epistemic_flexibility: float
    institutional_resilience: float
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
            "power_concentration":
                self.power_concentration,
            "authority_drift":
                self.authority_drift,
            "bad_precedent_persistence":
                self.bad_precedent_persistence,
            "governance_transparency":
                self.governance_transparency,
            "epistemic_flexibility":
                self.epistemic_flexibility,
            "institutional_resilience":
                self.institutional_resilience,
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
    passed: bool,
    cls: InstitutionalGovernanceClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return (
            "DESI_INSTITUTIONALLY_ROBUST"
        )
    return "DESI_INSTITUTIONALLY_FRAGILE"


def build_report() -> V104Report:
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
        f"INFO: power_concentration "
        f"{m.power_concentration}",
        f"INFO: authority_drift "
        f"{m.authority_drift}",
        f"INFO: bad_precedent_persistence "
        f"{m.bad_precedent_persistence}",
        f"INFO: governance_transparency "
        f"{m.governance_transparency}",
        f"INFO: epistemic_flexibility "
        f"{m.epistemic_flexibility}",
        f"INFO: institutional_resilience "
        f"{m.institutional_resilience}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V104Report(
        final_classification=cls.value,
        power_concentration=(
            m.power_concentration
        ),
        authority_drift=m.authority_drift,
        bad_precedent_persistence=(
            m.bad_precedent_persistence
        ),
        governance_transparency=(
            m.governance_transparency
        ),
        epistemic_flexibility=(
            m.epistemic_flexibility
        ),
        institutional_resilience=(
            m.institutional_resilience
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_institutional_governance_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version": (
            "v10_4_institutional_"
            "governance_verdict"
        ),
        "institutional_governance_classes":
            list(
                INSTITUTIONAL_GOVERNANCE_CLASSES,
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
    "V104Report",
    (
        "build_institutional_"
        "governance_verdict_artifact"
    ),
    "build_report",
]
