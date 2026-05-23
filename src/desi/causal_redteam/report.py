"""Aufgabe 5 + 8 + recommendation + replay."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .cross_frame import (
    CrossFrameOutcome,
    CrossFrameSummary,
    run_cross_frame,
)
from .independence import IndependenceReport, run_independence_check
from .runner import (
    AdversarialOutcome,
    AttackMetrics,
    GuardPressureMap,
    compute_metrics,
    compute_pressure_map,
    run_attacks,
)


@dataclass(frozen=True)
class RedTeamReport:
    started_at: datetime
    finished_at: datetime
    total_cases: int
    independence: IndependenceReport
    metrics: AttackMetrics
    pressure_map: GuardPressureMap
    cross_frame_summary: CrossFrameSummary
    outcomes: tuple[AdversarialOutcome, ...]
    cross_frame_outcomes: tuple[CrossFrameOutcome, ...]
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
            "pressure_map": self.pressure_map.to_dict(),
            "cross_frame_summary": self.cross_frame_summary.to_dict(),
            "outcomes": [o.to_dict() for o in self.outcomes],
            "cross_frame_outcomes":
                [c.to_dict() for c in self.cross_frame_outcomes],
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


def _decide(
    independence: IndependenceReport,
    metrics: AttackMetrics,
) -> tuple[str, str]:
    issues: list[str] = []
    if not independence.independence_passed:
        issues.append(f"independence: {independence.reason}")
    if metrics.attack_success_count != 0:
        issues.append(
            f"attack_success_count={metrics.attack_success_count} != 0"
        )
    if metrics.false_support_count != 0:
        issues.append(
            f"false_support_count={metrics.false_support_count} != 0"
        )
    if metrics.trap_block_rate != 1.0:
        issues.append(
            f"trap_block_rate={metrics.trap_block_rate} != 1.0"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return "CAUSAL_CHAIN_RED_TEAM_PASSED", "all hard gates clear"


def build_redteam_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> RedTeamReport:
    independence = run_independence_check()
    outcomes = run_attacks()
    metrics = compute_metrics(outcomes)
    pressure = compute_pressure_map(outcomes)
    cf_summary, cf_outcomes = run_cross_frame(outcomes)
    rec, reason = _decide(independence, metrics)

    payload = {
        "total_cases": len(outcomes),
        "independence": independence.to_dict(),
        "metrics": metrics.to_dict(),
        "pressure_map": pressure.to_dict(),
        "cross_frame_summary": cf_summary.to_dict(),
        "outcomes": [o.to_dict() for o in outcomes],
        "cross_frame_outcomes": [c.to_dict() for c in cf_outcomes],
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return RedTeamReport(
        started_at=started_at,
        finished_at=finished_at,
        total_cases=len(outcomes),
        independence=independence,
        metrics=metrics,
        pressure_map=pressure,
        cross_frame_summary=cf_summary,
        outcomes=outcomes,
        cross_frame_outcomes=cf_outcomes,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "RedTeamReport",
    "build_redteam_report",
]
