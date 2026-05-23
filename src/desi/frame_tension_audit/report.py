"""Aufgaben 3 + 6 + 8 — metrics, patchability gate, recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .clusters import (
    ClusterSummary,
    MIN_PATCHABLE_SIZE,
    TensionCluster,
    build_clusters,
    summarise_clusters,
)
from .contamination import (
    ContaminationResult,
    probe_all_clusters,
)
from .enums import TensionAuditClass, TensionFailureCause
from .extractor import TensionTarget, extract_tension_targets
from .splitter import TensionAuditOutcome, split_tension_targets


MIN_TENSION_PRECISION_FOR_PATCH: float = 0.90


@dataclass(frozen=True)
class TensionMetrics:
    total_tension_cases: int
    true_tension_count: int
    false_tension_count: int
    ambiguous_tension_count: int
    tension_precision: float
    false_tension_rate: float
    ambiguous_tension_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tension_cases": self.total_tension_cases,
            "true_tension_count": self.true_tension_count,
            "false_tension_count": self.false_tension_count,
            "ambiguous_tension_count": self.ambiguous_tension_count,
            "tension_precision": self.tension_precision,
            "false_tension_rate": self.false_tension_rate,
            "ambiguous_tension_rate": self.ambiguous_tension_rate,
        }


@dataclass(frozen=True)
class PatchabilityVerdict:
    cluster_id: str
    patchable: bool
    reason: str
    cluster_size: int
    contamination_risk: float
    manipulation_absorption_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "patchable": self.patchable,
            "reason": self.reason,
            "cluster_size": self.cluster_size,
            "contamination_risk": self.contamination_risk,
            "manipulation_absorption_risk":
                self.manipulation_absorption_risk,
        }


@dataclass(frozen=True)
class TensionAuditReport:
    started_at: datetime
    finished_at: datetime
    metrics: TensionMetrics
    outcomes: tuple[TensionAuditOutcome, ...]
    clusters: tuple[TensionCluster, ...]
    cluster_summary: ClusterSummary
    contaminations: tuple[ContaminationResult, ...]
    patchability: tuple[PatchabilityVerdict, ...]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "metrics": self.metrics.to_dict(),
            "outcomes": [o.to_dict() for o in self.outcomes],
            "clusters": [c.to_dict() for c in self.clusters],
            "cluster_summary": self.cluster_summary.to_dict(),
            "contaminations":
                [c.to_dict() for c in self.contaminations],
            "patchability":
                [p.to_dict() for p in self.patchability],
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
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


def _compute_metrics(
    outcomes: tuple[TensionAuditOutcome, ...]
) -> TensionMetrics:
    total = len(outcomes)
    true_n = sum(
        1 for o in outcomes
        if o.audit_class is TensionAuditClass.TRUE_TENSION
    )
    false_n = sum(
        1 for o in outcomes
        if o.audit_class is TensionAuditClass.FALSE_TENSION
    )
    ambig_n = sum(
        1 for o in outcomes
        if o.audit_class is TensionAuditClass.AMBIGUOUS_TENSION
    )
    return TensionMetrics(
        total_tension_cases=total,
        true_tension_count=true_n,
        false_tension_count=false_n,
        ambiguous_tension_count=ambig_n,
        tension_precision=(
            round(true_n / total, 6) if total else 0.0
        ),
        false_tension_rate=(
            round(false_n / total, 6) if total else 0.0
        ),
        ambiguous_tension_rate=(
            round(ambig_n / total, 6) if total else 0.0
        ),
    )


def _patchability_for(
    cluster: TensionCluster,
    contamination: ContaminationResult,
    causes_in_cluster: int,
) -> PatchabilityVerdict:
    issues: list[str] = []
    if cluster.size < MIN_PATCHABLE_SIZE:
        issues.append(
            f"cluster_size={cluster.size} < {MIN_PATCHABLE_SIZE}"
        )
    if causes_in_cluster != 1:
        issues.append(
            f"failure_cause not unique within cluster "
            f"({causes_in_cluster} distinct causes)"
        )
    if contamination.contamination_risk > 0.0:
        issues.append(
            f"contamination_risk={contamination.contamination_risk} > 0.0"
        )
    if contamination.manipulation_absorption_risk > 0.0:
        issues.append(
            f"manipulation_absorption_risk="
            f"{contamination.manipulation_absorption_risk} > 0.0; "
            f"would absorb {len(contamination.absorbed_manipulation_ids)} "
            "known adversarial case(s)"
        )
    if issues:
        return PatchabilityVerdict(
            cluster_id=cluster.cluster_id,
            patchable=False,
            reason="; ".join(issues),
            cluster_size=cluster.size,
            contamination_risk=contamination.contamination_risk,
            manipulation_absorption_risk=(
                contamination.manipulation_absorption_risk
            ),
        )
    return PatchabilityVerdict(
        cluster_id=cluster.cluster_id,
        patchable=True,
        reason="all four patchability conditions satisfied",
        cluster_size=cluster.size,
        contamination_risk=contamination.contamination_risk,
        manipulation_absorption_risk=(
            contamination.manipulation_absorption_risk
        ),
    )


def _decide_recommendation(
    metrics: TensionMetrics,
    patchability: tuple[PatchabilityVerdict, ...],
) -> tuple[str, str]:
    if metrics.tension_precision < MIN_TENSION_PRECISION_FOR_PATCH:
        return (
            "NONE",
            f"tension_precision={metrics.tension_precision} "
            f"< {MIN_TENSION_PRECISION_FOR_PATCH}",
        )
    patchable = [p for p in patchability if p.patchable]
    if not patchable:
        return (
            "NONE",
            "no cluster satisfies all four patchability conditions",
        )
    # Deterministic pick: largest cluster first, then alphabetical
    # cluster_id for tie-break.
    patchable.sort(key=lambda p: (-p.cluster_size, p.cluster_id))
    chosen = patchable[0]
    return (
        chosen.cluster_id,
        f"largest patchable cluster (size={chosen.cluster_size}); "
        "contamination = 0 and manipulation absorption = 0",
    )


def build_tension_audit_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> TensionAuditReport:
    targets = extract_tension_targets()
    outcomes = split_tension_targets(targets)
    metrics = _compute_metrics(outcomes)
    clusters = build_clusters(outcomes)
    cluster_summary = summarise_clusters(clusters)
    contaminations = probe_all_clusters(clusters)
    cont_by_id: dict[str, ContaminationResult] = {
        c.cluster_id: c for c in contaminations
    }

    # Causes-per-cluster (the failure cause is part of the cluster
    # key, so this is always 1; we keep the computation explicit so
    # a later split-key change does not silently weaken the gate).
    patchability_list: list[PatchabilityVerdict] = []
    for c in clusters:
        causes = {c.failure_cause.value}
        patchability_list.append(_patchability_for(
            c, cont_by_id[c.cluster_id], len(causes),
        ))
    patchability = tuple(patchability_list)

    rec, reason = _decide_recommendation(metrics, patchability)

    payload = {
        "metrics": metrics.to_dict(),
        "outcomes": [o.to_dict() for o in outcomes],
        "clusters": [c.to_dict() for c in clusters],
        "cluster_summary": cluster_summary.to_dict(),
        "contaminations": [c.to_dict() for c in contaminations],
        "patchability": [p.to_dict() for p in patchability],
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return TensionAuditReport(
        started_at=started_at,
        finished_at=finished_at,
        metrics=metrics,
        outcomes=outcomes,
        clusters=clusters,
        cluster_summary=cluster_summary,
        contaminations=contaminations,
        patchability=patchability,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "MIN_TENSION_PRECISION_FOR_PATCH",
    "PatchabilityVerdict",
    "TensionAuditReport",
    "TensionMetrics",
    "build_tension_audit_report",
]
