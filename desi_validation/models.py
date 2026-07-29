from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ItemType(str, Enum):
    OBSERVATION = "observation"
    INFERENCE = "inference"
    ASSUMPTION = "assumption"


class ValidationDecision(str, Enum):
    ADMISSIBLE = "admissible"
    HYPOTHESIS = "retained_as_hypothesis"
    REQUIRES_VERIFICATION = "requiring_further_verification"
    CONTRADICTED = "contradicted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvidenceAnchor:
    anchor_id: str
    source_id: str
    content_hash: str
    locator: str = ""
    polarity: str = "support"  # support | counter

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EvidenceAnchor":
        return cls(
            anchor_id=str(value.get("anchor_id", "")),
            source_id=str(value.get("source_id", "")),
            content_hash=str(value.get("content_hash", "")),
            locator=str(value.get("locator", "")),
            polarity=str(value.get("polarity", "support")),
        )


@dataclass(frozen=True)
class EpistemicItem:
    item_id: str
    item_type: ItemType
    text: str
    evidence_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EpistemicItem":
        return cls(
            item_id=str(value.get("item_id", "")),
            item_type=ItemType(str(value.get("item_type", "assumption"))),
            text=str(value.get("text", "")),
            evidence_ids=tuple(str(item) for item in value.get("evidence_ids", [])),
        )


@dataclass(frozen=True)
class CandidateUpdate:
    candidate_id: str
    claim: str
    items: tuple[EpistemicItem, ...]
    evidence: tuple[EvidenceAnchor, ...]
    source_trace_ids: tuple[str, ...]
    policy_ids: tuple[str, ...] = ()
    applicability_boundary: str = ""
    proposed_target: str = "L3"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CandidateUpdate":
        return cls(
            candidate_id=str(value.get("candidate_id", "")),
            claim=str(value.get("claim", "")),
            items=tuple(EpistemicItem.from_dict(item) for item in value.get("items", [])),
            evidence=tuple(EvidenceAnchor.from_dict(item) for item in value.get("evidence", [])),
            source_trace_ids=tuple(str(item) for item in value.get("source_trace_ids", [])),
            policy_ids=tuple(str(item) for item in value.get("policy_ids", [])),
            applicability_boundary=str(value.get("applicability_boundary", "")),
            proposed_target=str(value.get("proposed_target", "L3")),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class ValidationResult:
    candidate_id: str
    decision: ValidationDecision
    reasons: tuple[str, ...]
    required_verification: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    input_hash: str
    ruleset_version: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        return value
