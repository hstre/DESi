"""v37.1 - Semantic Audit Risk Benchmark report.

Pflichtmetriken (directive § v37.1):

* semantic_risk_visibility
* narrative_tension_detection
* implicit_inconsistency_detection
* uncertainty_preservation
* replay_stability

Killerfrage: "Kann DESi semantisch verdaechtige Finanzsituationen
erkennen, ohne zu halluzinieren?"

Surfaces semantic risks from explicit scenario signals: revenue
recognition, going concern, cashflow-vs-narrative, debt/footnote
inconsistency, implicit inconsistencies and narrative tensions. Every
risk is a flag that requires evidence - never a fraud assertion.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .risk_detector import (
    all_flags, detect_types, provenance, risk_scenarios,
)

VERDICT_PASSED = "SEMANTIC_RISK_RUN_PASSED"
VERDICT_PARTIAL = "SEMANTIC_RISK_RUN_PARTIAL"
VERDICT_HALT = "SEMANTIC_RISK_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.85


def _detected(scenario: dict) -> set[str]:
    return set(detect_types(scenario.get("signals", {})))


def _expected(scenario: dict) -> set[str]:
    return set(scenario.get("expected_risks", []))


def semantic_risk_visibility() -> float:
    """Recall of expected risks across all scenarios (every expected
    risk surfaced)."""
    total = 0
    found = 0
    for s in risk_scenarios():
        exp = _expected(s)
        det = _detected(s)
        total += len(exp)
        found += len(exp & det)
    return round(found / total, 6) if total else 0.0


def _typed_detection(risk_type: str) -> float:
    relevant = [
        s for s in risk_scenarios() if risk_type in _expected(s)
    ]
    if not relevant:
        return 1.0
    ok = sum(1 for s in relevant if risk_type in _detected(s))
    return round(ok / len(relevant), 6)


def narrative_tension_detection() -> float:
    return _typed_detection("narrative_tension")


def implicit_inconsistency_detection() -> float:
    return _typed_detection("implicit_inconsistency")


def uncertainty_preservation() -> float:
    """Every surfaced risk is a flag that requires evidence - no risk
    is asserted as a definitive conclusion."""
    flags = all_flags()
    if not flags:
        return 0.0
    ok = sum(
        1 for f in flags
        if f.severity == "flag" and f.requires_evidence
    )
    return round(ok / len(flags), 6)


def replay_stability() -> float:
    a = [(s["scenario_id"], tuple(sorted(_detected(s))))
         for s in risk_scenarios()]
    b = [(s["scenario_id"], tuple(sorted(_detected(s))))
         for s in risk_scenarios()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def risk_metrics() -> dict[str, float]:
    return {
        "semantic_risk_visibility": semantic_risk_visibility(),
        "narrative_tension_detection": narrative_tension_detection(),
        "implicit_inconsistency_detection":
            implicit_inconsistency_detection(),
        "uncertainty_preservation": uncertainty_preservation(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = risk_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = risk_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if m["uncertainty_preservation"] < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V371Report:
    scenario_count: int
    flag_count: int
    semantic_risk_visibility: float
    narrative_tension_detection: float
    implicit_inconsistency_detection: float
    uncertainty_preservation: float
    replay_stability: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_count": self.scenario_count,
            "flag_count": self.flag_count,
            "semantic_risk_visibility": self.semantic_risk_visibility,
            "narrative_tension_detection":
                self.narrative_tension_detection,
            "implicit_inconsistency_detection":
                self.implicit_inconsistency_detection,
            "uncertainty_preservation": self.uncertainty_preservation,
            "replay_stability": self.replay_stability,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V371Report:
    m = risk_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or m["uncertainty_preservation"] < 1.0
    rationale = (
        f"INFO: surfaced semantic risks across {len(risk_scenarios())}"
        f" scenarios (provenance {provenance()}); {len(all_flags())} "
        f"risk flags, all requiring evidence",
        f"{'PASS' if m['semantic_risk_visibility'] >= _FLOOR else 'FAIL'}"
        f": semantic_risk_visibility {m['semantic_risk_visibility']} "
        f">= 0.85",
        f"{'PASS' if m['narrative_tension_detection'] >= _FLOOR else 'FAIL'}"
        f": narrative_tension_detection "
        f"{m['narrative_tension_detection']} >= 0.85",
        f"{'PASS' if m['implicit_inconsistency_detection'] >= _FLOOR else 'FAIL'}"
        f": implicit_inconsistency_detection "
        f"{m['implicit_inconsistency_detection']} >= 0.85",
        f"{'PASS' if m['uncertainty_preservation'] >= _FLOOR else 'FAIL'}"
        f": uncertainty_preservation {m['uncertainty_preservation']} "
        f">= 0.85 (risks are flags, never fraud assertions)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V371Report(
        scenario_count=len(risk_scenarios()),
        flag_count=len(all_flags()),
        semantic_risk_visibility=m["semantic_risk_visibility"],
        narrative_tension_detection=m["narrative_tension_detection"],
        implicit_inconsistency_detection=(
            m["implicit_inconsistency_detection"]
        ),
        uncertainty_preservation=m["uncertainty_preservation"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_risk_artifact() -> dict[str, object]:
    m = risk_metrics()
    return {
        "schema_version": "v37_1_semantic_risk_run",
        "disclaimer": (
            "Semantic audit risk run over locally-vendored synthetic "
            "scenarios. DESi surfaces semantic risks (revenue "
            "recognition, going concern, cashflow-vs-narrative, "
            "debt/footnote inconsistency, implicit inconsistency, "
            "narrative tension) from explicit structured signals - "
            "no fuzzy NLP, no hallucination. Every risk is a flag "
            "that REQUIRES evidence and marks uncertainty; DESi never "
            "asserts fraud or a definitive conclusion. The scenarios "
            "are NOT official exam content and NO official results "
            "are claimed; this does not replace auditors. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "risk_flags": [f.to_dict() for f in all_flags()],
        "semantic_risk_visibility": m["semantic_risk_visibility"],
        "narrative_tension_detection": m["narrative_tension_detection"],
        "implicit_inconsistency_detection":
            m["implicit_inconsistency_detection"],
        "uncertainty_preservation": m["uncertainty_preservation"],
        "replay_stability": m["replay_stability"],
        "governance_identity": governance_identity(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V371Report",
    "build_report",
    "build_risk_artifact",
    "implicit_inconsistency_detection",
    "narrative_tension_detection",
    "risk_metrics",
    "semantic_risk_visibility",
    "uncertainty_preservation",
    "replay_stability",
]
