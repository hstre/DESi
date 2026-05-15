"""AnchorCoverageReport — Aufgabe 9 input."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .schema import ClaimAnchor, LegacyExemption
from .validator import AnchorOutcome, AnchorVerdict


@dataclass(frozen=True)
class AnchorCoverageReport:
    started_at: datetime
    finished_at: datetime
    total_documents: int
    total_anchors: int
    verified_anchors: int
    invalid_anchors: int
    legacy_exemptions: int
    verdict_counts: dict[str, int]
    anchors: tuple[AnchorOutcome, ...] = field(default_factory=tuple)
    legacy: tuple[LegacyExemption, ...] = field(default_factory=tuple)
    replay_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_documents": self.total_documents,
            "total_anchors": self.total_anchors,
            "verified_anchors": self.verified_anchors,
            "invalid_anchors": self.invalid_anchors,
            "legacy_exemptions": self.legacy_exemptions,
            "verdict_counts": dict(self.verdict_counts),
            "anchors": [a.to_dict() for a in self.anchors],
            "legacy": [l.to_dict() for l in self.legacy],
            "replay_hash": self.replay_hash,
        }


def compute_report_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_anchor_report(
    *,
    outcomes: tuple[AnchorOutcome, ...],
    legacy: tuple[LegacyExemption, ...],
    document_count: int,
    started_at: datetime,
    finished_at: datetime,
) -> AnchorCoverageReport:
    counter: Counter[AnchorVerdict] = Counter(
        o.verdict for o in outcomes
    )
    verified = counter.get(AnchorVerdict.VERIFIED, 0)
    invalid = sum(
        c for v, c in counter.items() if v is not AnchorVerdict.VERIFIED
    )
    verdict_counts = {v.value: counter.get(v, 0) for v in AnchorVerdict}
    payload = {
        "total_documents": document_count,
        "total_anchors": len(outcomes),
        "verified_anchors": verified,
        "invalid_anchors": invalid,
        "legacy_exemptions": len(legacy),
        "verdict_counts": verdict_counts,
        "anchors": [o.to_dict() for o in outcomes],
        "legacy": [l.to_dict() for l in legacy],
    }
    return AnchorCoverageReport(
        started_at=started_at,
        finished_at=finished_at,
        total_documents=document_count,
        total_anchors=len(outcomes),
        verified_anchors=verified,
        invalid_anchors=invalid,
        legacy_exemptions=len(legacy),
        verdict_counts=verdict_counts,
        anchors=outcomes,
        legacy=legacy,
        replay_hash=compute_report_replay_hash(payload),
    )


__all__ = [
    "AnchorCoverageReport",
    "build_anchor_report",
    "compute_report_replay_hash",
]
