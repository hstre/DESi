"""v13.4 — Scientific Integrity verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``scientific_integrity_score``
* ``sludge_resistance``
* ``false_accusation_rate``
* ``epistemic_integrity``
* ``replay_stability``

Killerfrage: "Kann ein epistemisches System
Wissenschaft gegen epistemischen Muell
verteidigen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    SCIENTIFIC_INTEGRITY_CLASSES,
    ScientificIntegrityClass,
)


@dataclass(frozen=True)
class V134Report:
    final_classification: str
    fake_paper_recall: float
    false_accusation_rate: float
    citation_grounding: float
    epistemic_integrity: float
    sludge_propagation: float
    sludge_resistance: float
    scientific_integrity_score: float
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
            "fake_paper_recall":
                self.fake_paper_recall,
            "false_accusation_rate":
                self.false_accusation_rate,
            "citation_grounding":
                self.citation_grounding,
            "epistemic_integrity":
                self.epistemic_integrity,
            "sludge_propagation":
                self.sludge_propagation,
            "sludge_resistance":
                self.sludge_resistance,
            "scientific_integrity_score":
                (
                    self
                    .scientific_integrity_score
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
    passed: bool,
    cls: ScientificIntegrityClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_INTEGRITY_DEFENDER"
    return "DESI_SLUDGE_COMPATIBLE"


def build_report() -> V134Report:
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
        f"INFO: fake_paper_recall "
        f"{m.fake_paper_recall}",
        f"INFO: false_accusation_rate "
        f"{m.false_accusation_rate}",
        f"INFO: citation_grounding "
        f"{m.citation_grounding}",
        f"INFO: epistemic_integrity "
        f"{m.epistemic_integrity}",
        f"INFO: sludge_propagation "
        f"{m.sludge_propagation}",
        f"INFO: sludge_resistance "
        f"{m.sludge_resistance}",
        f"INFO: scientific_integrity_score "
        f"{m.scientific_integrity_score}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V134Report(
        final_classification=cls.value,
        fake_paper_recall=m.fake_paper_recall,
        false_accusation_rate=(
            m.false_accusation_rate
        ),
        citation_grounding=(
            m.citation_grounding
        ),
        epistemic_integrity=(
            m.epistemic_integrity
        ),
        sludge_propagation=(
            m.sludge_propagation
        ),
        sludge_resistance=(
            m.sludge_resistance
        ),
        scientific_integrity_score=(
            m.scientific_integrity_score
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_scientific_integrity_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version": (
            "v13_4_scientific_"
            "integrity_verdict"
        ),
        "scientific_integrity_classes":
            list(
                SCIENTIFIC_INTEGRITY_CLASSES,
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
    "V134Report",
    (
        "build_scientific_integrity_"
        "verdict_artifact"
    ),
    "build_report",
]
