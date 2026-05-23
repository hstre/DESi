"""v11.4 — Chess Governance verdict report.

Five Pflichtmetriken:

* ``final_classification``
* ``compute_efficiency_gain``
* ``quality_preservation``
* ``search_governance_integrity``
* ``replay_stability``

Killerfrage: "Kann DESi Suchraeume epistemisch
komprimieren, ohne relevante Information zu
verlieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import (
    CHESS_GOVERNANCE_CLASSES,
    ChessGovernanceClass,
)


@dataclass(frozen=True)
class V114Report:
    final_classification: str
    compute_reduction: float
    quality_preservation: float
    tactical_miss_rate: float
    pv_stability: float
    search_governance_integrity: float
    compute_efficiency_gain: float
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
            "compute_reduction":
                self.compute_reduction,
            "quality_preservation":
                self.quality_preservation,
            "tactical_miss_rate":
                self.tactical_miss_rate,
            "pv_stability":
                self.pv_stability,
            "search_governance_integrity":
                (
                    self
                    .search_governance_integrity
                ),
            "compute_efficiency_gain":
                self.compute_efficiency_gain,
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
    cls: ChessGovernanceClass,
    replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if passed:
        return "DESI_SEARCH_COMPRESSOR"
    return "DESI_BRUTE_FORCE_DEPENDENT"


def build_report() -> V114Report:
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
        f"INFO: compute_reduction "
        f"{m.compute_reduction}",
        f"INFO: quality_preservation "
        f"{m.quality_preservation}",
        f"INFO: tactical_miss_rate "
        f"{m.tactical_miss_rate}",
        f"INFO: pv_stability "
        f"{m.pv_stability}",
        f"INFO: search_governance_integrity "
        f"{m.search_governance_integrity}",
        f"INFO: compute_efficiency_gain "
        f"{m.compute_efficiency_gain}",
        f"INFO: replay_stability "
        f"{m.replay_stability}",
        f"{'PASS' if passed else 'FAIL'}: "
        f"gate_passes_all (failing="
        f"{list(failing)})",
        f"{'PASS' if replay_meta == 1.0 else 'FAIL'}"
        f": meta_replay_stability "
        f"{replay_meta}",
    )
    return V114Report(
        final_classification=cls.value,
        compute_reduction=(
            m.compute_reduction
        ),
        quality_preservation=(
            m.quality_preservation
        ),
        tactical_miss_rate=(
            m.tactical_miss_rate
        ),
        pv_stability=m.pv_stability,
        search_governance_integrity=(
            m.search_governance_integrity
        ),
        compute_efficiency_gain=(
            m.compute_efficiency_gain
        ),
        replay_stability=m.replay_stability,
        gate_passes_all=passed,
        failing_conditions=failing,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_chess_governance_verdict_artifact(
) -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version":
            "v11_4_chess_governance_verdict",
        "chess_governance_classes":
            list(CHESS_GOVERNANCE_CLASSES),
        "final_classification":
            classify().value,
        "metrics": m.to_dict(),
        "gate_passes_all":
            gate_passes_all(),
        "failing_conditions":
            list(gate_failing_conditions()),
    }


__all__ = [
    "V114Report",
    "build_chess_governance_verdict_artifact",
    "build_report",
]
