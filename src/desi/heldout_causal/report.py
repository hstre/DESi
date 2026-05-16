"""Aufgaben 5 + 8 — hard gates + recommendation + replay hash."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .independence import IndependenceReport, run_independence_check
from .runner import (
    HeldoutMetrics,
    HeldoutOutcome,
    compute_metrics,
    run_heldout,
)


MIN_PRECISION: float = 0.95
MIN_RECALL: float = 0.85


@dataclass(frozen=True)
class HeldoutReport:
    started_at: datetime
    finished_at: datetime
    total_cases: int
    independence: IndependenceReport
    metrics: HeldoutMetrics
    outcomes: tuple[HeldoutOutcome, ...]
    failure_classes: dict[str, int]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_cases": self.total_cases,
            "independence": self.independence.to_dict(),
            "metrics": self.metrics.to_dict(),
            "outcomes": [o.to_dict() for o in self.outcomes],
            "failure_classes": dict(self.failure_classes),
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


def _decide_recommendation(
    independence: IndependenceReport,
    metrics: HeldoutMetrics,
) -> tuple[str, str]:
    issues: list[str] = []
    if not independence.independence_passed:
        issues.append(f"independence: {independence.reason}")
    if metrics.heldout_precision < MIN_PRECISION:
        issues.append(
            f"precision={metrics.heldout_precision} < {MIN_PRECISION}"
        )
    if metrics.heldout_recall < MIN_RECALL:
        issues.append(
            f"recall={metrics.heldout_recall} < {MIN_RECALL}"
        )
    if metrics.false_positive_count != 0:
        issues.append(
            f"false_positive_count={metrics.false_positive_count} != 0"
        )
    if metrics.trap_block_rate != 1.0:
        issues.append(
            f"trap_block_rate={metrics.trap_block_rate} != 1.0"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return (
        "CAUSAL_CHAIN_GENERALISED",
        "all five hard gates passed",
    )


def build_heldout_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> HeldoutReport:
    independence = run_independence_check()
    outcomes = run_heldout()
    metrics = compute_metrics(outcomes)

    failure_classes: dict[str, int] = {}
    for o in outcomes:
        if o.failure_class is not None:
            failure_classes[o.failure_class.value] = (
                failure_classes.get(o.failure_class.value, 0) + 1
            )

    rec, reason = _decide_recommendation(independence, metrics)

    payload = {
        "total_cases": len(outcomes),
        "independence": independence.to_dict(),
        "metrics": metrics.to_dict(),
        "outcomes": [o.to_dict() for o in outcomes],
        "failure_classes": dict(sorted(failure_classes.items())),
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return HeldoutReport(
        started_at=started_at,
        finished_at=finished_at,
        total_cases=len(outcomes),
        independence=independence,
        metrics=metrics,
        outcomes=outcomes,
        failure_classes=dict(sorted(failure_classes.items())),
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "HeldoutReport",
    "MIN_PRECISION",
    "MIN_RECALL",
    "build_heldout_report",
]
