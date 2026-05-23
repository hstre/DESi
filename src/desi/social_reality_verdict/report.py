"""v7.4 — Social Reality verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``social_resilience``
* ``epistemic_integrity``
* ``governance_stability``
* ``replay_stability``

Killerfrage: "Kann DESi epistemisch integer
bleiben, wenn die soziale Realitaet epistemische
Integritaet bestraft?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    SOCIAL_REALITY_CLASSES, SocialRealityClass,
)


@dataclass(frozen=True)
class V74Report:
    final_classification: str
    false_certainty_rate: float
    identity_bias: float
    virality_bias: float
    governance_survival: float
    governance_stability: float
    epistemic_integrity: float
    social_resilience: float
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
            "false_certainty_rate":
                self.false_certainty_rate,
            "identity_bias":
                self.identity_bias,
            "virality_bias":
                self.virality_bias,
            "governance_survival":
                self.governance_survival,
            "governance_stability":
                self.governance_stability,
            "epistemic_integrity":
                self.epistemic_integrity,
            "social_resilience":
                self.social_resilience,
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
    passed: bool, cls: SocialRealityClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_SOCIALLY_ROBUST"
    return "DESI_SOCIALLY_FRAGILE"


def build_report() -> V74Report:
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
        f"INFO: false_certainty_rate "
        f"{m.false_certainty_rate}",
        f"INFO: identity_bias "
        f"{m.identity_bias}",
        f"INFO: virality_bias "
        f"{m.virality_bias}",
        f"INFO: governance_survival "
        f"{m.governance_survival}",
        f"INFO: governance_stability "
        f"{m.governance_stability}",
        f"INFO: epistemic_integrity "
        f"{m.epistemic_integrity}",
        f"INFO: social_resilience "
        f"{m.social_resilience}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V74Report(
        final_classification=cls.value,
        false_certainty_rate=(
            m.false_certainty_rate
        ),
        identity_bias=m.identity_bias,
        virality_bias=m.virality_bias,
        governance_survival=(
            m.governance_survival
        ),
        governance_stability=(
            m.governance_stability
        ),
        epistemic_integrity=(
            m.epistemic_integrity
        ),
        social_resilience=(
            m.social_resilience
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_social_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v7_4_social_verdict",
        "social_reality_classes":
            list(SOCIAL_REALITY_CLASSES),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V74Report",
    "build_report",
    "build_social_verdict_artifact",
]
