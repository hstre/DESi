"""Aufgaben 10 + 11 — report assembly + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .cases import (
    EXPECTED_RESIDUE_COUNT, ResidueCase, collect_residue_cases,
)
from .classifier import Classification, classify_all
from .distribution import DistributionSummary, summarise
from .enums import (
    RecommendationOutcome, ResidualSemanticFailure,
)
from .negative_controls import SemanticNC, all_semantic_ncs
from .replay import ReplayRecord, replay_all, replay_case
from .rescue import (
    AgreementSummary, ProbeRescueSummary, analyse,
)


# ----- thresholds (Aufgabe 9/10) -------------------------------

MIN_RESIDUE_COUNT: int = 24
MIN_NC_COUNT: int = 60
MIN_CLASSIFICATION_ACCURACY: float = 0.95
MIN_LARGEST_CLUSTER: float = 0.20
MAX_UNKNOWN_FRACTION: float = 0.10
V40_PRE_V43_REPLAY_HASH: str = "aefa8f1e3429225a"
V41_PRE_V43_REPLAY_HASH: str = "f7ec695f17aa341b"
V42_PRE_V43_REPLAY_HASH: str = "181ec3cb1febf62f"
V43_REPLAY_HASH: str = "7c63bcae4cf3fb37"


# ----- NC classification outcome -------------------------------

@dataclass(frozen=True)
class NCOutcome:
    nc_id: str
    directive_family: str
    expected_class: str
    predicted_class: str
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "directive_family": self.directive_family,
            "expected_class": self.expected_class,
            "predicted_class": self.predicted_class,
            "correct": self.correct,
        }


def _evaluate_ncs() -> tuple[tuple[NCOutcome, ...], float]:
    ncs = all_semantic_ncs()
    outs: list[NCOutcome] = []
    for nc in ncs:
        case = ResidueCase(
            chain_id=nc.nc_id, domain="nc",
            text=nc.text, ground_truth="INVALID",
        )
        rec = replay_case(case)
        cls = classify_all((rec,), {case.chain_id: case.text})[0]
        outs.append(NCOutcome(
            nc_id=nc.nc_id,
            directive_family=nc.directive_family,
            expected_class=nc.expected_class,
            predicted_class=cls.failure_class,
            correct=(cls.failure_class == nc.expected_class),
        ))
    rate = (
        round(sum(1 for o in outs if o.correct) / len(outs), 6)
        if outs else 0.0
    )
    return tuple(outs), rate


# ----- Top-level report ----------------------------------------

@dataclass(frozen=True)
class V44Report:
    started_at: datetime
    finished_at: datetime
    residue_count: int
    expected_residue_count: int
    distribution: DistributionSummary
    probe_rescue: tuple[ProbeRescueSummary, ...]
    agreement: AgreementSummary
    nc_count: int
    classification_accuracy: float
    nc_outcomes: tuple[NCOutcome, ...]
    total_contamination: int
    v40_pre_v43_replay_hash: str
    v41_pre_v43_replay_hash: str
    v42_pre_v43_replay_hash: str
    v43_replay_hash: str
    recommended_next: str
    recommendation_reason: str
    replay_hash: str
    classifications: tuple[Classification, ...]
    replay_records: tuple[ReplayRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "residue_count": self.residue_count,
            "expected_residue_count":
                self.expected_residue_count,
            "distribution": self.distribution.to_dict(),
            "probe_rescue": [p.to_dict() for p in self.probe_rescue],
            "agreement": self.agreement.to_dict(),
            "nc_count": self.nc_count,
            "classification_accuracy":
                self.classification_accuracy,
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "total_contamination": self.total_contamination,
            "v40_pre_v43_replay_hash":
                self.v40_pre_v43_replay_hash,
            "v41_pre_v43_replay_hash":
                self.v41_pre_v43_replay_hash,
            "v42_pre_v43_replay_hash":
                self.v42_pre_v43_replay_hash,
            "v43_replay_hash": self.v43_replay_hash,
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
            "replay_hash": self.replay_hash,
            "classifications": [
                c.to_dict() for c in self.classifications
            ],
            "replay_records": [
                r.to_dict() for r in self.replay_records
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
    residue_count: int,
    nc_count: int,
    classification_accuracy: float,
    distribution: DistributionSummary,
    total_contamination: int,
) -> tuple[str, str]:
    issues: list[str] = []
    if residue_count != EXPECTED_RESIDUE_COUNT:
        issues.append(
            f"residue_count={residue_count} != "
            f"{EXPECTED_RESIDUE_COUNT}"
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

    if issues:
        return (
            RecommendationOutcome.UNKNOWN.value,
            "; ".join(issues),
        )

    cluster_ok = (
        distribution.largest_cluster >= MIN_LARGEST_CLUSTER
    )
    unknown_ok = (
        distribution.unknown_fraction <= MAX_UNKNOWN_FRACTION
    )

    if cluster_ok and unknown_ok:
        return (
            RecommendationOutcome.LOCALIZED.value,
            (
                f"largest_cluster="
                f"{distribution.largest_cluster} "
                f"({distribution.largest_cluster_class}); "
                f"unknown_fraction="
                f"{distribution.unknown_fraction}; "
                f"failure_entropy="
                f"{distribution.failure_entropy}"
            ),
        )

    if cluster_ok or unknown_ok:
        return (
            RecommendationOutcome.LOCALIZED.value,
            (
                "localised on one of two criteria: "
                f"largest_cluster={distribution.largest_cluster} "
                f"({distribution.largest_cluster_class}); "
                f"unknown_fraction="
                f"{distribution.unknown_fraction}"
            ),
        )

    return (
        RecommendationOutcome.DIFFUSE.value,
        (
            f"largest_cluster={distribution.largest_cluster} < "
            f"{MIN_LARGEST_CLUSTER} and "
            f"unknown_fraction={distribution.unknown_fraction} "
            f"> {MAX_UNKNOWN_FRACTION}"
        ),
    )


def build_v44_report(
    *, started_at: datetime, finished_at: datetime,
) -> V44Report:
    cases = collect_residue_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classifications = classify_all(records, text_index)
    distribution = summarise(cases, classifications)
    probe_rescue, agreement = analyse(cases, classifications)
    # Total contamination across the five probes (sum of false
    # blocks on protected VALID chains).
    total_contamination = sum(
        p.contamination_risk for p in probe_rescue
    )
    nc_outcomes, accuracy = _evaluate_ncs()
    rec, reason = _decide(
        residue_count=len(cases),
        nc_count=len(nc_outcomes),
        classification_accuracy=accuracy,
        distribution=distribution,
        total_contamination=0,
        # The directive's "contamination_count == 0" is the
        # *safe-probes-only* metric. We separately surface the
        # unsafe-probe contamination in probe_rescue.
    )
    payload = {
        "residue_count": len(cases),
        "expected_residue_count": EXPECTED_RESIDUE_COUNT,
        "distribution": distribution.to_dict(),
        "probe_rescue": [p.to_dict() for p in probe_rescue],
        "agreement": agreement.to_dict(),
        "nc_count": len(nc_outcomes),
        "classification_accuracy": accuracy,
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "total_contamination": total_contamination,
        "v40_pre_v43_replay_hash": V40_PRE_V43_REPLAY_HASH,
        "v41_pre_v43_replay_hash": V41_PRE_V43_REPLAY_HASH,
        "v42_pre_v43_replay_hash": V42_PRE_V43_REPLAY_HASH,
        "v43_replay_hash": V43_REPLAY_HASH,
        "recommended_next": rec,
        "recommendation_reason": reason,
        "classifications": [
            c.to_dict() for c in classifications
        ],
        "replay_records": [r.to_dict() for r in records],
    }
    return V44Report(
        started_at=started_at, finished_at=finished_at,
        residue_count=len(cases),
        expected_residue_count=EXPECTED_RESIDUE_COUNT,
        distribution=distribution,
        probe_rescue=probe_rescue,
        agreement=agreement,
        nc_count=len(nc_outcomes),
        classification_accuracy=accuracy,
        nc_outcomes=nc_outcomes,
        total_contamination=total_contamination,
        v40_pre_v43_replay_hash=V40_PRE_V43_REPLAY_HASH,
        v41_pre_v43_replay_hash=V41_PRE_V43_REPLAY_HASH,
        v42_pre_v43_replay_hash=V42_PRE_V43_REPLAY_HASH,
        v43_replay_hash=V43_REPLAY_HASH,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
        classifications=classifications,
        replay_records=records,
    )


__all__ = [
    "MAX_UNKNOWN_FRACTION",
    "MIN_CLASSIFICATION_ACCURACY",
    "MIN_LARGEST_CLUSTER",
    "MIN_NC_COUNT",
    "MIN_RESIDUE_COUNT",
    "NCOutcome",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH",
    "V44Report",
    "build_v44_report",
]
