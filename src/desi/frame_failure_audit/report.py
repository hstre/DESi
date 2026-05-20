"""FrameFailureAuditReport + recommend_next — Aufgaben 7 + 9."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..frames import FrameDetector
from .clusters import (
    ClusterSummary,
    FailureCluster,
    FrameBreakdown,
    build_clusters,
    per_frame_breakdown,
)
from .extractor import FrameFailureRecord, extract_failures
from .negative_control import NEGATIVE_CONTROLS
from .patchability import (
    PatchabilityVerdict,
    assess_patchability,
    probe_contamination,
)


@dataclass(frozen=True)
class NegativeControlOutcome:
    nc_id: str
    detected_frame: str
    expected_frame: str
    pass_: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "nc_id": self.nc_id,
            "detected_frame": self.detected_frame,
            "expected_frame": self.expected_frame,
            "pass": self.pass_,
        }


@dataclass(frozen=True)
class FrameFailureAuditReport:
    started_at: datetime
    finished_at: datetime
    total_failures: int
    failures: tuple[FrameFailureRecord, ...]
    cluster_summary: ClusterSummary
    per_frame_breakdown: tuple[FrameBreakdown, ...]
    patchability: tuple[PatchabilityVerdict, ...]
    negative_control_outcomes: tuple[NegativeControlOutcome, ...]
    negative_control_precision: float
    recommended_next: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_failures": self.total_failures,
            "failures": [f.to_dict() for f in self.failures],
            "cluster_summary": self.cluster_summary.to_dict(),
            "per_frame_breakdown":
                [b.to_dict() for b in self.per_frame_breakdown],
            "patchability":
                [p.to_dict() for p in self.patchability],
            "negative_control_outcomes":
                [n.to_dict() for n in self.negative_control_outcomes],
            "negative_control_precision":
                self.negative_control_precision,
            "recommended_next": self.recommended_next,
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _run_negative_controls() -> tuple[
    tuple[NegativeControlOutcome, ...], float,
]:
    """A negative-control passes iff the detector does NOT classify
    the lookalike as the decoy frame — i.e. a hypothetical patch
    that recovers ``decoy_for_frame`` would not absorb this case.
    Refusing to commit (FRAME_UNDECLARED) also counts as
    "not absorbed", which is the conservative safe behaviour."""
    detector = FrameDetector()
    outcomes: list[NegativeControlOutcome] = []
    correct = 0
    for nc in NEGATIVE_CONTROLS:
        decl = detector.detect(claim_id=nc.nc_id, source_text=nc.text)
        ok = decl.frame_kind is not nc.decoy_for_frame
        outcomes.append(NegativeControlOutcome(
            nc_id=nc.nc_id,
            detected_frame=decl.frame_kind.value,
            expected_frame=nc.expected_frame.value,
            pass_=ok,
        ))
        if ok:
            correct += 1
    precision = round(correct / len(outcomes), 6) if outcomes else 0.0
    return tuple(outcomes), precision


def _recommend_next(
    verdicts: tuple[PatchabilityVerdict, ...],
    nc_precision: float,
) -> str:
    if nc_precision < 1.0:
        return "NONE"
    safe = [v for v in verdicts if v.safe_patch_candidate]
    if not safe:
        return "NONE"
    # Deterministic order: first safe candidate by cluster_id sort.
    safe.sort(key=lambda v: v.cluster_id)
    return safe[0].cluster_id


def build_audit_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> FrameFailureAuditReport:
    failures = extract_failures()
    cluster_summary = build_clusters(failures)
    breakdown = per_frame_breakdown(failures)

    verdicts: list[PatchabilityVerdict] = []
    for cluster in cluster_summary.clusters:
        verdicts.append(assess_patchability(cluster, failures))

    nc_outcomes, nc_precision = _run_negative_controls()
    recommended = _recommend_next(tuple(verdicts), nc_precision)

    payload = {
        "total_failures": len(failures),
        "failures": [f.to_dict() for f in failures],
        "cluster_summary": cluster_summary.to_dict(),
        "per_frame_breakdown": [b.to_dict() for b in breakdown],
        "patchability": [v.to_dict() for v in verdicts],
        "negative_control_outcomes":
            [n.to_dict() for n in nc_outcomes],
        "negative_control_precision": nc_precision,
        "recommended_next": recommended,
    }
    return FrameFailureAuditReport(
        started_at=started_at,
        finished_at=finished_at,
        total_failures=len(failures),
        failures=failures,
        cluster_summary=cluster_summary,
        per_frame_breakdown=breakdown,
        patchability=tuple(verdicts),
        negative_control_outcomes=nc_outcomes,
        negative_control_precision=nc_precision,
        recommended_next=recommended,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "FrameFailureAuditReport",
    "NegativeControlOutcome",
    "build_audit_report",
]
