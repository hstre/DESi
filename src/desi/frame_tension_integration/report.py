"""Aufgaben 8 + 9 — score function + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .corpus import CorpusCase, build_corpus, corpus_summary
from .enums import InsertionPoint
from .scoring import InsertionMetrics, compute_metrics
from .simulators import SimulationOutcome, simulate_all_points


MIN_MANIPULATION_BLOCK_RATE: float = 0.95
MAX_FALSE_BLOCK_RATE: float = 0.05


@dataclass(frozen=True)
class IntegrationProbeReport:
    started_at: datetime
    finished_at: datetime
    corpus_total: int
    corpus_adversarial: int
    corpus_by_origin: dict[str, int]
    per_point_metrics: dict[str, dict[str, Any]]
    per_point_outcomes: dict[str, list[dict[str, Any]]]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "corpus_total": self.corpus_total,
            "corpus_adversarial": self.corpus_adversarial,
            "corpus_by_origin": dict(self.corpus_by_origin),
            "per_point_metrics": dict(self.per_point_metrics),
            "per_point_outcomes": dict(self.per_point_outcomes),
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
    per_point: dict[InsertionPoint, InsertionMetrics],
) -> tuple[str, str]:
    # Sort by integration_score desc, then point name asc for
    # deterministic tie-break.
    ranked = sorted(
        per_point.items(),
        key=lambda kv: (-kv[1].integration_score, kv[0].value),
    )
    top_point, top_metrics = ranked[0]

    issues: list[str] = []
    if top_metrics.contamination_risk != 0.0:
        issues.append(
            f"contamination_risk={top_metrics.contamination_risk} != 0.0"
        )
    if top_metrics.manipulation_block_rate < MIN_MANIPULATION_BLOCK_RATE:
        issues.append(
            f"manipulation_block_rate="
            f"{top_metrics.manipulation_block_rate} "
            f"< {MIN_MANIPULATION_BLOCK_RATE}"
        )
    if top_metrics.false_block_rate > MAX_FALSE_BLOCK_RATE:
        issues.append(
            f"false_block_rate={top_metrics.false_block_rate} "
            f"> {MAX_FALSE_BLOCK_RATE}"
        )
    if issues:
        return (
            "NONE",
            f"best-scoring point {top_point.value} fails gates: "
            + "; ".join(issues),
        )
    return (
        top_point.value,
        f"highest integration_score ({top_metrics.integration_score}) "
        f"with zero contamination, manipulation_block_rate="
        f"{top_metrics.manipulation_block_rate}, false_block_rate="
        f"{top_metrics.false_block_rate}",
    )


def build_integration_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> IntegrationProbeReport:
    cs = build_corpus()
    summary = corpus_summary()
    all_outcomes = simulate_all_points(cs)
    per_point_metrics: dict[InsertionPoint, InsertionMetrics] = {}
    for point, outs in all_outcomes.items():
        per_point_metrics[point] = compute_metrics(point, outs)
    metrics_dict: dict[str, dict[str, Any]] = {}
    outcomes_dict: dict[str, list[dict[str, Any]]] = {}
    for point in InsertionPoint:
        metrics_dict[point.value] = per_point_metrics[point].to_dict()
        outcomes_dict[point.value] = [
            o.to_dict() for o in all_outcomes[point]
        ]

    rec, reason = _decide_recommendation(per_point_metrics)

    payload = {
        "corpus_total": summary["total"],
        "corpus_adversarial": summary["adversarial"],
        "corpus_by_origin": summary["by_origin"],
        "per_point_metrics": metrics_dict,
        "per_point_outcomes": outcomes_dict,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return IntegrationProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        corpus_total=summary["total"],
        corpus_adversarial=summary["adversarial"],
        corpus_by_origin=summary["by_origin"],
        per_point_metrics=metrics_dict,
        per_point_outcomes=outcomes_dict,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "IntegrationProbeReport",
    "MAX_FALSE_BLOCK_RATE",
    "MIN_MANIPULATION_BLOCK_RATE",
    "build_integration_report",
]
