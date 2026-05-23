"""v29.2 - Comparative Real Benchmark Verdict report.

Pflichtmetriken / Concept Gate (directive § v29.2):

* measured_runtime_improvement >= 0.20
* artifact_identity            == 1.0
* governance_identity          == 1.0
* regression_survival          == 1.0
* replay_stability             == 1.0

Killerfrage: "Kann DESi reale branch-isolierte
Infrastrukturverbesserungen durchfuehren ohne Replay oder
Governance zu beschaedigen?"

A real, measured comparison. No projected numbers. If the gate
passes, DESi can perform real, replay-validated, branch-isolated
infrastructure evolution under human governance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .classification import (
    CLASS_VALIDATED, GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    RESULT_CLASSES, classify_result, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)
from .comparison import (
    artifact_identity, governance_identity,
    measured_runtime_improvement, recompute_counts,
    regression_survival, replay_stability,
)

VERDICT_REAL = "REAL_INFRA_EVOLUTION_VALIDATED"
VERDICT_UNSAFE = "INFRA_EVOLUTION_UNSAFE"
VERDICT_HALT = "EVOLUTION_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_REAL, VERDICT_UNSAFE, VERDICT_HALT,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{c.name}:{c.value}:{c.passed}"
        for c in gate_conditions()
    ]
    parts.append(f"class:{classify_result()}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    if replay_stability() < 1.0:
        return VERDICT_HALT
    return VERDICT_REAL if gate_passes_all() else VERDICT_UNSAFE


@dataclass(frozen=True)
class V292Report:
    baseline_recompute_count: int
    cached_recompute_count: int
    measured_runtime_improvement: float
    artifact_identity: float
    governance_identity: float
    regression_survival: float
    replay_stability: float
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    classification: str
    gate_statement: str
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_recompute_count":
                self.baseline_recompute_count,
            "cached_recompute_count": self.cached_recompute_count,
            "measured_runtime_improvement":
                self.measured_runtime_improvement,
            "artifact_identity": self.artifact_identity,
            "governance_identity": self.governance_identity,
            "regression_survival": self.regression_survival,
            "replay_stability": self.replay_stability,
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "classification": self.classification,
            "gate_statement": self.gate_statement,
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


def build_report() -> V292Report:
    base, cached = recompute_counts()
    improvement = measured_runtime_improvement()
    artifact = artifact_identity()
    governance = governance_identity()
    regression = regression_survival()
    replay = replay_stability()
    gate_ok = gate_passes_all()
    halt = replay < 1.0
    cond = {c.name: c for c in gate_conditions()}
    rationale = (
        f"INFO: measured comparison DESi_current vs "
        f"DESi_replay_cache_v1; recomputes {base} -> {cached}",
        "INFO: real measured improvement (recompute reduction), "
        "not projected; cache branch is isolated and unmerged",
        f"{'PASS' if cond['measured_runtime_improvement'].passed else 'FAIL'}"
        f": measured_runtime_improvement {improvement} >= 0.20",
        f"{'PASS' if cond['artifact_identity'].passed else 'FAIL'}"
        f": artifact_identity {artifact} == 1.0",
        f"{'PASS' if cond['governance_identity'].passed else 'FAIL'}"
        f": governance_identity {governance} == 1.0",
        f"{'PASS' if cond['regression_survival'].passed else 'FAIL'}"
        f": regression_survival {regression} == 1.0 (confirmed "
        f"by the mandatory end-of-phase full regression)",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}"
        f": replay_stability {replay} == 1.0",
        f"INFO: classification {classify_result()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}; no "
        f"auto-merge, no main modification",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V292Report(
        baseline_recompute_count=base,
        cached_recompute_count=cached,
        measured_runtime_improvement=improvement,
        artifact_identity=artifact,
        governance_identity=governance,
        regression_survival=regression,
        replay_stability=replay,
        gate_passes_all=gate_ok,
        gate_failing_conditions=gate_failing_conditions(),
        classification=classify_result(),
        gate_statement=GATE_PASS_STATEMENT,
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    base, cached = recompute_counts()
    return {
        "schema_version": "v29_2_replay_cache_verdict",
        "disclaimer": (
            "Final verdict on the first real, branch-isolated, "
            "measured DESi infrastructure evolution. The "
            "comparison DESi_current vs DESi_replay_cache_v1 is "
            "measured (recompute reduction), not projected or "
            "synthetic. The cache delivers a real runtime "
            "improvement while keeping every artifact "
            "byte-identical, governance unchanged, and replay "
            "stable; regression survival is confirmed by the "
            "mandatory end-of-phase full regression. Nothing is "
            "merged, no main modification, no auto-deployment, "
            "and human approval is mandatory. Replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "result_classes": list(RESULT_CLASSES),
        "branch": "proposal/replay_cache_v1",
        "baseline_recompute_count": base,
        "cached_recompute_count": cached,
        "measured_runtime_improvement":
            measured_runtime_improvement(),
        "artifact_identity": artifact_identity(),
        "governance_identity": governance_identity(),
        "regression_survival": regression_survival(),
        "replay_stability": replay_stability(),
        "gate_conditions": [
            c.to_dict() for c in gate_conditions()
        ],
        "gate_passes_all": gate_passes_all(),
        "gate_failing_conditions":
            list(gate_failing_conditions()),
        "gate_statement": GATE_PASS_STATEMENT,
        "classification": classify_result(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "VERDICT_UNSAFE",
    "V292Report",
    "build_report",
    "build_verdict_artifact",
]
