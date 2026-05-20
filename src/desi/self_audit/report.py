"""SelfAuditReport — Aufgabe 7."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .claim import ClaimVerdict, ReplayedClaim
from .contradictions import Contradiction
from .corpus import DocumentArtifact
from .drift import DriftFinding


@dataclass(frozen=True)
class SelfAuditReport:
    started_at: datetime
    finished_at: datetime
    total_documents: int
    total_claims: int
    verified_claims: int
    unverifiable_claims: int
    hash_mismatch_claims: int
    value_mismatch_claims: int
    ambiguous_claims: int
    contradictions_count: int
    drift_findings_count: int
    self_deception_rate: float
    documents: tuple[DocumentArtifact, ...] = field(default_factory=tuple)
    replayed_claims: tuple[ReplayedClaim, ...] = field(default_factory=tuple)
    contradictions: tuple[Contradiction, ...] = field(default_factory=tuple)
    drift_findings: tuple[DriftFinding, ...] = field(default_factory=tuple)
    replay_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_documents": self.total_documents,
            "total_claims": self.total_claims,
            "verified_claims": self.verified_claims,
            "unverifiable_claims": self.unverifiable_claims,
            "hash_mismatch_claims": self.hash_mismatch_claims,
            "value_mismatch_claims": self.value_mismatch_claims,
            "ambiguous_claims": self.ambiguous_claims,
            "contradictions_count": self.contradictions_count,
            "drift_findings_count": self.drift_findings_count,
            "self_deception_rate": self.self_deception_rate,
            "documents": [d.to_dict() for d in self.documents],
            "replayed_claims":
                [r.to_dict() for r in self.replayed_claims],
            "contradictions":
                [c.to_dict() for c in self.contradictions],
            "drift_findings":
                [d.to_dict() for d in self.drift_findings],
            "replay_hash": self.replay_hash,
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_audit_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_audit_report(
    *,
    documents: tuple[DocumentArtifact, ...],
    replayed_claims: tuple[ReplayedClaim, ...],
    contradictions: tuple[Contradiction, ...],
    drift_findings: tuple[DriftFinding, ...],
    started_at: datetime,
    finished_at: datetime,
) -> SelfAuditReport:
    counter: Counter[ClaimVerdict] = Counter(
        r.verdict for r in replayed_claims
    )
    total = len(replayed_claims)
    verified = counter.get(ClaimVerdict.VERIFIED, 0)
    missing = counter.get(ClaimVerdict.MISSING_ARTIFACT, 0)
    hash_mm = counter.get(ClaimVerdict.HASH_MISMATCH, 0)
    value_mm = counter.get(ClaimVerdict.VALUE_MISMATCH, 0)
    ambiguous = counter.get(ClaimVerdict.AMBIGUOUS_REFERENCE, 0)
    unverifiable = missing + hash_mm + value_mm + ambiguous

    self_deception = _ratio(unverifiable, total)

    payload = {
        "total_documents": len(documents),
        "total_claims": total,
        "verified_claims": verified,
        "unverifiable_claims": unverifiable,
        "hash_mismatch_claims": hash_mm,
        "value_mismatch_claims": value_mm,
        "ambiguous_claims": ambiguous,
        "contradictions_count": len(contradictions),
        "drift_findings_count": len(drift_findings),
        "self_deception_rate": self_deception,
        "documents": [d.to_dict() for d in documents],
        "replayed_claims": [r.to_dict() for r in replayed_claims],
        "contradictions": [c.to_dict() for c in contradictions],
        "drift_findings": [d.to_dict() for d in drift_findings],
    }
    return SelfAuditReport(
        started_at=started_at,
        finished_at=finished_at,
        total_documents=len(documents),
        total_claims=total,
        verified_claims=verified,
        unverifiable_claims=unverifiable,
        hash_mismatch_claims=hash_mm,
        value_mismatch_claims=value_mm,
        ambiguous_claims=ambiguous,
        contradictions_count=len(contradictions),
        drift_findings_count=len(drift_findings),
        self_deception_rate=self_deception,
        documents=documents,
        replayed_claims=replayed_claims,
        contradictions=contradictions,
        drift_findings=drift_findings,
        replay_hash=compute_audit_replay_hash(payload),
    )


__all__ = [
    "SelfAuditReport",
    "build_audit_report",
    "compute_audit_replay_hash",
]
