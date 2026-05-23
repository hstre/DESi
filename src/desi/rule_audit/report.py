"""RuleCoverageReport — final v2.5 artifact (Aufgabe 6 + replay)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .categories import MissingRuleClass
from .metrics import (
    RuleCoverageMetrics,
    compute_rule_coverage_metrics,
    dominant_missing_rule_class,
)
from .runner import RuleCoverageRun
from .trace import RuleCoverageTrace


@dataclass(frozen=True)
class RuleCoverageReport:
    started_at: datetime
    finished_at: datetime
    total_cases: int
    rule_hit_rate: float
    no_rule_match_rate: float
    parser_vs_rule_misclassification_rate: float
    per_rule_hit_counts: dict[str, int]
    missing_rule_distribution: dict[str, int]
    per_category_rule_coverage: dict[str, dict[str, int]]
    multi_hop_case_coverage: float
    dominant_missing_rule_class: MissingRuleClass
    traces: tuple[RuleCoverageTrace, ...] = field(default_factory=tuple)
    replay_hash: str = ""
    reflection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_cases": self.total_cases,
            "rule_hit_rate": self.rule_hit_rate,
            "no_rule_match_rate": self.no_rule_match_rate,
            "parser_vs_rule_misclassification_rate":
                self.parser_vs_rule_misclassification_rate,
            "per_rule_hit_counts": dict(self.per_rule_hit_counts),
            "missing_rule_distribution": dict(self.missing_rule_distribution),
            "per_category_rule_coverage": {
                k: dict(v)
                for k, v in self.per_category_rule_coverage.items()
            },
            "multi_hop_case_coverage": self.multi_hop_case_coverage,
            "dominant_missing_rule_class":
                self.dominant_missing_rule_class.value,
            "traces": [t.to_dict() for t in self.traces],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


def compute_report_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_rule_coverage_report(
    run: RuleCoverageRun,
    *,
    started_at: datetime,
    finished_at: datetime,
) -> RuleCoverageReport:
    metrics: RuleCoverageMetrics = compute_rule_coverage_metrics(run)
    dominant = dominant_missing_rule_class(metrics)
    payload = {
        "total_cases": metrics.total,
        "rule_hit_rate": metrics.rule_hit_rate,
        "no_rule_match_rate": metrics.no_rule_match_rate,
        "parser_vs_rule_misclassification_rate":
            metrics.parser_vs_rule_misclassification_rate,
        "per_rule_hit_counts": metrics.per_rule_hit_counts,
        "missing_rule_distribution": metrics.missing_rule_distribution,
        "per_category_rule_coverage": metrics.per_category_rule_coverage,
        "multi_hop_case_coverage": metrics.multi_hop_case_coverage,
        "dominant_missing_rule_class": dominant.value,
        "traces": [t.to_dict() for t in run.traces],
    }
    replay_hash = compute_report_replay_hash(payload)
    return RuleCoverageReport(
        started_at=started_at,
        finished_at=finished_at,
        total_cases=metrics.total,
        rule_hit_rate=metrics.rule_hit_rate,
        no_rule_match_rate=metrics.no_rule_match_rate,
        parser_vs_rule_misclassification_rate=(
            metrics.parser_vs_rule_misclassification_rate
        ),
        per_rule_hit_counts=metrics.per_rule_hit_counts,
        missing_rule_distribution=metrics.missing_rule_distribution,
        per_category_rule_coverage=metrics.per_category_rule_coverage,
        multi_hop_case_coverage=metrics.multi_hop_case_coverage,
        dominant_missing_rule_class=dominant,
        traces=run.traces,
        replay_hash=replay_hash,
    )


__all__ = [
    "RuleCoverageReport",
    "build_rule_coverage_report",
    "compute_report_replay_hash",
]
