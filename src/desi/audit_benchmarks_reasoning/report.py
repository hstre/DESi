"""v37.2 - Audit Reasoning & Evidence Benchmark report.

Pflichtmetriken (directive § v37.2):

* evidence_gap_visibility
* unsupported_conclusion_resistance
* assertion_mapping_integrity
* materiality_traceability
* replay_stability

Killerfrage: "Kann DESi auditartige Begruendungsketten strukturieren,
ohne epistemische Luecken zu verstecken?"

Maps audit assertions, surfaces evidence gaps, proposes procedures to
close them, and reasons about materiality - never drawing a supported
conclusion where evidence is missing.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .audit_assertion_mapping import (
    assertion_mapping_integrity, audit_tasks, provenance,
)
from .audit_procedure_generator import all_procedures
from .evidence_gap_detection import (
    conclusion, evidence_gap_visibility, gap_tasks,
    unsupported_conclusion_resistance,
)
from .materiality_reasoning import is_material, materiality_traceability

VERDICT_PASSED = "AUDIT_REASONING_RUN_PASSED"
VERDICT_PARTIAL = "AUDIT_REASONING_RUN_PARTIAL"
VERDICT_HALT = "AUDIT_REASONING_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.85


def replay_stability() -> float:
    a = [(t.task_id, conclusion(t), is_material(t)) for t in audit_tasks()]
    b = [(t.task_id, conclusion(t), is_material(t)) for t in audit_tasks()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def reasoning_metrics() -> dict[str, float]:
    return {
        "evidence_gap_visibility": evidence_gap_visibility(),
        "unsupported_conclusion_resistance":
            unsupported_conclusion_resistance(),
        "assertion_mapping_integrity": assertion_mapping_integrity(),
        "materiality_traceability": materiality_traceability(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = reasoning_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = reasoning_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if m["unsupported_conclusion_resistance"] < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V372Report:
    task_count: int
    gap_count: int
    evidence_gap_visibility: float
    unsupported_conclusion_resistance: float
    assertion_mapping_integrity: float
    materiality_traceability: float
    replay_stability: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "gap_count": self.gap_count,
            "evidence_gap_visibility": self.evidence_gap_visibility,
            "unsupported_conclusion_resistance":
                self.unsupported_conclusion_resistance,
            "assertion_mapping_integrity":
                self.assertion_mapping_integrity,
            "materiality_traceability": self.materiality_traceability,
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


def build_report() -> V372Report:
    m = reasoning_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or m["unsupported_conclusion_resistance"] < 1.0
    rationale = (
        f"INFO: mapped {len(audit_tasks())} audit assertions "
        f"(provenance {provenance()}); {len(gap_tasks())} tasks have "
        f"an evidence gap, each given conclusion "
        f"'insufficient_evidence' with a proposed procedure",
        f"{'PASS' if m['evidence_gap_visibility'] >= _FLOOR else 'FAIL'}"
        f": evidence_gap_visibility {m['evidence_gap_visibility']} "
        f">= 0.85 (gaps surfaced)",
        f"{'PASS' if m['unsupported_conclusion_resistance'] >= _FLOOR else 'FAIL'}"
        f": unsupported_conclusion_resistance "
        f"{m['unsupported_conclusion_resistance']} >= 0.85 (no "
        f"conclusion without evidence)",
        f"{'PASS' if m['assertion_mapping_integrity'] >= _FLOOR else 'FAIL'}"
        f": assertion_mapping_integrity "
        f"{m['assertion_mapping_integrity']} >= 0.85",
        f"{'PASS' if m['materiality_traceability'] >= _FLOOR else 'FAIL'}"
        f": materiality_traceability {m['materiality_traceability']} "
        f">= 0.85",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V372Report(
        task_count=len(audit_tasks()),
        gap_count=len(gap_tasks()),
        evidence_gap_visibility=m["evidence_gap_visibility"],
        unsupported_conclusion_resistance=(
            m["unsupported_conclusion_resistance"]
        ),
        assertion_mapping_integrity=m["assertion_mapping_integrity"],
        materiality_traceability=m["materiality_traceability"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_reasoning_artifact() -> dict[str, object]:
    m = reasoning_metrics()
    return {
        "schema_version": "v37_2_audit_reasoning_run",
        "disclaimer": (
            "Audit reasoning & evidence run over locally-vendored "
            "synthetic tasks (assertions, evidence, materiality). "
            "DESi maps each audit assertion, surfaces every evidence "
            "gap, proposes a procedure to close it, and reasons "
            "about materiality from amount vs threshold. Where "
            "evidence is missing, the conclusion is "
            "'insufficient_evidence' - DESi never draws a supported "
            "conclusion without evidence and never creates false "
            "certainty. NOT official exam content; NO official "
            "results claimed; does not replace auditors. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "conclusions": {
            t.task_id: conclusion(t) for t in audit_tasks()
        },
        "materiality": {
            t.task_id: is_material(t) for t in audit_tasks()
        },
        "proposed_procedures": all_procedures(),
        "evidence_gap_visibility": m["evidence_gap_visibility"],
        "unsupported_conclusion_resistance":
            m["unsupported_conclusion_resistance"],
        "assertion_mapping_integrity": m["assertion_mapping_integrity"],
        "materiality_traceability": m["materiality_traceability"],
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
    "V372Report",
    "build_reasoning_artifact",
    "build_report",
    "reasoning_metrics",
    "replay_stability",
]
