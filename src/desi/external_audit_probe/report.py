"""Aufgaben 10 + 11 — report assembly + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .cases import (
    FalseSupportCase, collect_false_support_cases,
)
from .classifier import Classification, classify_all
from .counterfactual import (
    ClusterCounterfactual, evaluate_all as cf_evaluate_all,
)
from .distribution import DistributionSummary, summarise
from .enums import ExternalAuditFailure, RecommendationOutcome
from .guards import (
    GuardPressure, GuardPressureSummary, measure_guard_pressure,
    summarise as guards_summarise,
)
from .negative_controls import (
    FailureFixture, all_failure_fixtures,
)
from .replay import ReplayRecord, replay_all, replay_case


# ----- Public thresholds (Aufgabe 10) ---------------------------

MIN_FALSE_SUPPORT_CASES: int = 100
MIN_NC_COUNT: int = 50
MIN_CLASSIFICATION_ACCURACY: float = 0.95
MIN_LARGEST_CLUSTER: float = 0.20
MAX_UNKNOWN_FRACTION: float = 0.10
EXPECTED_FALSE_SUPPORT_COUNT: int = 143
V40_REPLAY_HASH: str = "aefa8f1e3429225a"
V41_REPLAY_HASH: str = "f7ec695f17aa341b"


# ----- NC classification accuracy -------------------------------

@dataclass(frozen=True)
class NCClassificationOutcome:
    nc_id: str
    expected_class: str
    predicted_class: str
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "expected_class": self.expected_class,
            "predicted_class": self.predicted_class,
            "correct": self.correct,
        }


def _evaluate_ncs(
    fixtures: tuple[FailureFixture, ...],
) -> tuple[
    tuple[NCClassificationOutcome, ...], float,
]:
    # Wrap each NC into a FalseSupportCase so we can reuse the
    # replay + classifier path verbatim.
    cases = tuple(
        FalseSupportCase(
            chain_id=f.nc_id,
            domain="negative_control_synthetic",
            text=f.text, ground_truth="INVALID",
        )
        for f in fixtures
    )
    records = tuple(replay_case(c) for c in cases)
    classes = classify_all(
        records,
        {c.chain_id: c.text for c in cases},
    )
    out: list[NCClassificationOutcome] = []
    correct = 0
    for f, cls in zip(fixtures, classes):
        ok = cls.failure_class == f.expected_class
        if ok:
            correct += 1
        out.append(NCClassificationOutcome(
            nc_id=f.nc_id,
            expected_class=f.expected_class,
            predicted_class=cls.failure_class,
            correct=ok,
        ))
    rate = round(correct / len(out), 6) if out else 0.0
    return tuple(out), rate


# ----- Top-level report ----------------------------------------

@dataclass(frozen=True)
class V42Report:
    started_at: datetime
    finished_at: datetime
    case_count: int
    expected_case_count: int
    nc_count: int
    classification_accuracy: float
    nc_outcomes: tuple[NCClassificationOutcome, ...]
    distribution: DistributionSummary
    guard_pressure: GuardPressureSummary
    counterfactuals: tuple[ClusterCounterfactual, ...]
    total_contamination: int
    v40_replay_hash: str
    v41_replay_hash: str
    recommended_next: str
    recommendation_reason: str
    replay_hash: str
    classifications: tuple[Classification, ...]
    replay_records: tuple[ReplayRecord, ...]
    guard_records: tuple[GuardPressure, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "case_count": self.case_count,
            "expected_case_count": self.expected_case_count,
            "nc_count": self.nc_count,
            "classification_accuracy":
                self.classification_accuracy,
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "distribution": self.distribution.to_dict(),
            "guard_pressure": self.guard_pressure.to_dict(),
            "counterfactuals": [
                c.to_dict() for c in self.counterfactuals
            ],
            "total_contamination": self.total_contamination,
            "v40_replay_hash": self.v40_replay_hash,
            "v41_replay_hash": self.v41_replay_hash,
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
            "replay_hash": self.replay_hash,
            "classifications": [
                c.to_dict() for c in self.classifications
            ],
            "replay_records": [
                r.to_dict() for r in self.replay_records
            ],
            "guard_records": [
                g.to_dict() for g in self.guard_records
            ],
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _decide(
    *,
    case_count: int,
    nc_count: int,
    classification_accuracy: float,
    distribution: DistributionSummary,
    total_contamination: int,
) -> tuple[str, str]:
    issues: list[str] = []
    if case_count < MIN_FALSE_SUPPORT_CASES:
        issues.append(
            f"case_count={case_count} < "
            f"{MIN_FALSE_SUPPORT_CASES}"
        )
    if nc_count < MIN_NC_COUNT:
        issues.append(
            f"nc_count={nc_count} < {MIN_NC_COUNT}"
        )
    if classification_accuracy < MIN_CLASSIFICATION_ACCURACY:
        issues.append(
            f"classification_accuracy="
            f"{classification_accuracy} < "
            f"{MIN_CLASSIFICATION_ACCURACY}"
        )
    if total_contamination != 0:
        issues.append(
            f"total_contamination={total_contamination} != 0"
        )

    unknown_fraction = round(
        distribution.failure_count.get(
            ExternalAuditFailure.UNKNOWN.value, 0,
        ) / case_count, 6,
    ) if case_count else 1.0

    cluster_ok = (
        distribution.largest_cluster >= MIN_LARGEST_CLUSTER
    )
    unknown_ok = unknown_fraction <= MAX_UNKNOWN_FRACTION

    if issues:
        # Hard gate failure (corpus, NC, contamination, or
        # classifier accuracy) -> UNKNOWN result.
        return (
            RecommendationOutcome.UNKNOWN.value,
            "; ".join(issues),
        )

    if cluster_ok and unknown_ok:
        return (
            RecommendationOutcome.LOCALIZED.value,
            (
                f"largest_cluster="
                f"{distribution.largest_cluster} "
                f"({distribution.largest_cluster_class}); "
                f"unknown_fraction={unknown_fraction}; "
                f"failure_entropy="
                f"{distribution.failure_entropy}"
            ),
        )

    if unknown_ok or cluster_ok:
        return (
            RecommendationOutcome.LOCALIZED.value,
            (
                f"localised on one of two criteria: "
                f"largest_cluster={distribution.largest_cluster} "
                f"({distribution.largest_cluster_class}); "
                f"unknown_fraction={unknown_fraction}"
            ),
        )

    return (
        RecommendationOutcome.DIFFUSE.value,
        (
            f"largest_cluster={distribution.largest_cluster} < "
            f"{MIN_LARGEST_CLUSTER} and "
            f"unknown_fraction={unknown_fraction} > "
            f"{MAX_UNKNOWN_FRACTION}"
        ),
    )


def build_v42_report(
    *, started_at: datetime, finished_at: datetime,
) -> V42Report:
    cases = collect_false_support_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classifications = classify_all(records, text_index)
    strategy_origins = {
        r.chain_id: r.frame_strategy_origin for r in records
    }
    distribution = summarise(
        cases, classifications, strategy_origins,
    )
    guards = tuple(
        measure_guard_pressure(c, r)
        for c, r in zip(cases, records)
    )
    guard_summary = guards_summarise(guards)
    counterfactuals = cf_evaluate_all(cases, classifications)
    total_contam = sum(
        cf.contamination_risk for cf in counterfactuals
    )
    fixtures = all_failure_fixtures()
    nc_outcomes, nc_accuracy = _evaluate_ncs(fixtures)
    rec, reason = _decide(
        case_count=len(cases),
        nc_count=len(fixtures),
        classification_accuracy=nc_accuracy,
        distribution=distribution,
        total_contamination=total_contam,
    )
    payload = {
        "case_count": len(cases),
        "expected_case_count": EXPECTED_FALSE_SUPPORT_COUNT,
        "nc_count": len(fixtures),
        "classification_accuracy": nc_accuracy,
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "distribution": distribution.to_dict(),
        "guard_pressure": guard_summary.to_dict(),
        "counterfactuals": [
            cf.to_dict() for cf in counterfactuals
        ],
        "total_contamination": total_contam,
        "v40_replay_hash": V40_REPLAY_HASH,
        "v41_replay_hash": V41_REPLAY_HASH,
        "recommended_next": rec,
        "recommendation_reason": reason,
        "classifications": [
            c.to_dict() for c in classifications
        ],
        "replay_records": [r.to_dict() for r in records],
        "guard_records": [g.to_dict() for g in guards],
    }
    return V42Report(
        started_at=started_at, finished_at=finished_at,
        case_count=len(cases),
        expected_case_count=EXPECTED_FALSE_SUPPORT_COUNT,
        nc_count=len(fixtures),
        classification_accuracy=nc_accuracy,
        nc_outcomes=nc_outcomes,
        distribution=distribution,
        guard_pressure=guard_summary,
        counterfactuals=counterfactuals,
        total_contamination=total_contam,
        v40_replay_hash=V40_REPLAY_HASH,
        v41_replay_hash=V41_REPLAY_HASH,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
        classifications=classifications,
        replay_records=records,
        guard_records=guards,
    )


__all__ = [
    "EXPECTED_FALSE_SUPPORT_COUNT",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CLASSIFICATION_ACCURACY",
    "MIN_FALSE_SUPPORT_CASES",
    "MIN_LARGEST_CLUSTER",
    "MIN_NC_COUNT",
    "NCClassificationOutcome",
    "V40_REPLAY_HASH",
    "V41_REPLAY_HASH",
    "V42Report",
    "build_v42_report",
]
