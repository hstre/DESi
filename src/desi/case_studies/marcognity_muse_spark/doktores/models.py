"""Typed model for the adversarial Doktores audit of the DESi case study.

The audit is deterministic and offline: no LLM is called. The four "doctors" are
four source-anchored rule sets that attack the DESi analysis and try to refute,
revise or bound each finding. Confidence is qualitative (high/medium/low) because
the engine has no calibrated probabilities — an honest limit, stated rather than
faked.

Nothing here certifies the truth of the legal statements in the Muse text; the
audit assesses only the DESi case study's methodical traceability, internal
consistency, provenance and reach.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """The four adversarial reviewer roles (mapped onto rule sets, not LLMs)."""

    PROVENANCE_REVIEWER = "provenance_reviewer"        # Doktor 1 — claims + provenance
    METHODOLOGY_REVIEWER = "methodology_reviewer"      # Doktor 2 — setup + case study
    LOGIC_REVIEWER = "logic_reviewer"                  # Doktor 3 — logic + falsification
    FAIRNESS_REVIEWER = "fairness_reviewer"            # Doktor 4 — steelman + counter-position


class Decision(str, Enum):
    """A single doctor's decision on one item."""

    UPHOLD = "uphold"
    UPHOLD_WITH_QUALIFICATION = "uphold_with_qualification"
    REVISE = "revise"
    REJECT = "reject"
    INSUFFICIENT_MATERIAL = "insufficient_material"


class Consensus(str, Enum):
    """The synthesised cross-doctor decision on one item."""

    UPHOLD = "uphold"
    UPHOLD_WITH_QUALIFICATION = "uphold_with_qualification"
    REVISE = "revise"
    REJECT = "reject"
    UNRESOLVED = "unresolved"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(str, Enum):
    """Synthesis status for a top-level finding (the requested table)."""

    ROBUST = "robust"          # survives the audit; several reviewers confirm
    QUALIFIED = "qualified"    # core holds, wording too strong
    REVISE = "revise"          # classification or reach wrong
    REJECT = "reject"          # not covered by the material
    UNRESOLVED = "unresolved"  # data insufficient


class ContradictionClass(str, Enum):
    LOGICAL_CONTRADICTION = "logical_contradiction"
    EMPIRICAL_CONFLICT = "empirical_conflict"
    METHODICAL_INCONSISTENCY = "methodical_inconsistency"
    PIPELINE_INCONSISTENCY = "pipeline_inconsistency"
    UNSUBSTANTIATED_CLAIM = "unsubstantiated_claim"
    TERMINOLOGICAL_IMPRECISION = "terminological_imprecision"


class AttestationRating(str, Enum):
    PASSED = "passed"
    PASSED_WITH_QUALIFICATIONS = "passed_with_qualifications"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"
    NOT_ASSESSABLE = "not_assessable"


@dataclass(frozen=True)
class DoctorVerdict:
    role: Role
    decision: Decision
    reason: str
    source_anchors: tuple[str, ...]
    rule: str = ""              # the stated decision rule applied

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "decision": self.decision.value,
            "reason": self.reason,
            "source_anchors": list(self.source_anchors),
            "rule": self.rule,
        }


@dataclass(frozen=True)
class ClaimReview:
    claim_id: str
    original_desi_verdict: str
    doctor_verdicts: tuple[DoctorVerdict, ...]
    consensus: Consensus
    revised_verdict: str          # == original unless the audit overturns it
    confidence: Confidence
    dissent: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "original_desi_verdict": self.original_desi_verdict,
            "doctor_verdicts": [v.to_dict() for v in self.doctor_verdicts],
            "consensus": self.consensus.value,
            "revised_verdict": self.revised_verdict,
            "confidence": self.confidence.value,
            "dissent": list(self.dissent),
            "required_changes": list(self.required_changes),
        }


@dataclass(frozen=True)
class ContradictionReview:
    cid: str
    original_classification: str
    reviewed_classification: ContradictionClass
    upheld: bool                  # upheld AS the original (structural) classification
    reason: str
    source_anchors: tuple[str, ...]
    minority_opinion: str = ""
    report_change_required: bool = False
    confidence: Confidence = Confidence.MEDIUM

    def to_dict(self) -> dict:
        return {
            "id": self.cid,
            "original_classification": self.original_classification,
            "reviewed_classification": self.reviewed_classification.value,
            "upheld": self.upheld,
            "reason": self.reason,
            "source_anchors": list(self.source_anchors),
            "minority_opinion": self.minority_opinion,
            "report_change_required": self.report_change_required,
            "confidence": self.confidence.value,
        }


@dataclass(frozen=True)
class MethodologyFinding:
    topic: str
    decision: Decision
    assessment: str
    source_anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FairnessFinding:
    kind: str          # "steelman" | "overreach_flag"
    text: str
    source_anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynthesisFinding:
    finding: str
    status: FindingStatus
    rationale: str
    revisit_if: str = ""     # condition under which the verdict would change


@dataclass(frozen=True)
class AttestationDimension:
    dimension: str
    rating: AttestationRating
    reason: str


@dataclass(frozen=True)
class Revision:
    rid: str
    target_files: tuple[str, ...]
    before: str
    after: str
    audit_finding: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "id": self.rid,
            "target_files": list(self.target_files),
            "before": self.before,
            "after": self.after,
            "audit_finding": self.audit_finding,
            "reason": self.reason,
        }


__all__ = [
    "Role", "Decision", "Consensus", "Confidence", "FindingStatus",
    "ContradictionClass", "AttestationRating", "DoctorVerdict", "ClaimReview",
    "ContradictionReview", "MethodologyFinding", "FairnessFinding",
    "SynthesisFinding", "AttestationDimension", "Revision",
]
