"""v36.1 - Scientific Fact Checking (SciFact / QASper) report.

Pflichtmetriken (directive § v36.1):

* evidence_alignment
* unsupported_claim_rejection
* citation_integrity
* answer_grounding
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Aussagen pruefen, ohne
Evidenzluecken zu verdecken?"

Runs locally-vendored SciFact and QASper reference datasets through
DESi's deterministic evidence-to-label and answer-grounding
governance. Claims are only asserted when evidence supports them;
gaps surface as NOT_ENOUGH_INFO; unanswerable questions are flagged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .claim_verification import (
    answer_grounding, citation_integrity, evidence_alignment,
    unanswerable_flagged, unsupported_claim_rejection,
)
from .evidence_mapping import derive_label
from .qasper_loader import qasper_tasks
from .scifact_loader import scifact_tasks

VERDICT_PASSED = "SCIFACT_QASPER_RUN_PASSED"
VERDICT_PARTIAL = "SCIFACT_QASPER_RUN_PARTIAL"
VERDICT_HALT = "SCIFACT_QASPER_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.85


def replay_stability() -> float:
    a = [(t.claim_id, derive_label(t)) for t in scifact_tasks()]
    b = [(t.claim_id, derive_label(t)) for t in scifact_tasks()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def scifact_metrics() -> dict[str, float]:
    return {
        "evidence_alignment": evidence_alignment(),
        "unsupported_claim_rejection": unsupported_claim_rejection(),
        "citation_integrity": citation_integrity(),
        "answer_grounding": answer_grounding(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = scifact_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = scifact_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if not unanswerable_flagged():
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V361Report:
    scifact_count: int
    qasper_count: int
    evidence_alignment: float
    unsupported_claim_rejection: float
    citation_integrity: float
    answer_grounding: float
    replay_stability: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scifact_count": self.scifact_count,
            "qasper_count": self.qasper_count,
            "evidence_alignment": self.evidence_alignment,
            "unsupported_claim_rejection":
                self.unsupported_claim_rejection,
            "citation_integrity": self.citation_integrity,
            "answer_grounding": self.answer_grounding,
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


def build_report() -> V361Report:
    m = scifact_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or not unanswerable_flagged()
    rationale = (
        f"INFO: verified {len(scifact_tasks())} SciFact claims and "
        f"{len(qasper_tasks())} QASper questions through "
        f"deterministic evidence governance; no LLM",
        f"{'PASS' if m['evidence_alignment'] >= _FLOOR else 'FAIL'}: "
        f"evidence_alignment {m['evidence_alignment']} >= 0.85",
        f"{'PASS' if m['unsupported_claim_rejection'] >= _FLOOR else 'FAIL'}"
        f": unsupported_claim_rejection "
        f"{m['unsupported_claim_rejection']} >= 0.85 (evidence gaps "
        f"surfaced as NOT_ENOUGH_INFO)",
        f"{'PASS' if m['citation_integrity'] >= _FLOOR else 'FAIL'}: "
        f"citation_integrity {m['citation_integrity']} >= 0.85 (no "
        f"phantom evidence)",
        f"{'PASS' if m['answer_grounding'] >= _FLOOR else 'FAIL'}: "
        f"answer_grounding {m['answer_grounding']} >= 0.85 "
        f"(unanswerable flagged {unanswerable_flagged()})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V361Report(
        scifact_count=len(scifact_tasks()),
        qasper_count=len(qasper_tasks()),
        evidence_alignment=m["evidence_alignment"],
        unsupported_claim_rejection=m["unsupported_claim_rejection"],
        citation_integrity=m["citation_integrity"],
        answer_grounding=m["answer_grounding"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_scifact_artifact() -> dict[str, object]:
    m = scifact_metrics()
    return {
        "schema_version": "v36_1_scifact_qasper_run",
        "disclaimer": (
            "Scientific fact-checking run over locally-vendored "
            "SciFact and QASper reference datasets. DESi derives "
            "verdicts purely from the mapped evidence: a claim is "
            "asserted only when evidence supports it, evidence gaps "
            "surface as NOT_ENOUGH_INFO rather than being hidden, "
            "and unanswerable questions are flagged rather than "
            "fabricated. This tests deterministic evidence "
            "governance, not LLM accuracy; the datasets are NOT live "
            "downloads of the official suites and the scores are NOT "
            "official leaderboard results. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "scifact_labels": {
            t.claim_id: derive_label(t) for t in scifact_tasks()
        },
        "evidence_alignment": m["evidence_alignment"],
        "unsupported_claim_rejection": m["unsupported_claim_rejection"],
        "citation_integrity": m["citation_integrity"],
        "answer_grounding": m["answer_grounding"],
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
    "V361Report",
    "build_report",
    "build_scifact_artifact",
    "scifact_metrics",
]
