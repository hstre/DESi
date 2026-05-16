"""Aufgaben 5 + 8 + 11 + 12 — report assembly +
recommendation gate."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .enums import (
    RecommendationOutcome, ReproducibilityClass, ToolReproPolicy,
)
from .environment import EnvironmentFingerprint, fingerprint
from .negative_controls import (
    all_repro_ncs, classification_accuracy, classify_nc,
)
from .replay_matrix import MatrixEntry, build_matrix
from .tool_policy import (
    TOOL_REPRO_POLICY, expected_correct_count,
)


MIN_NC_COUNT: int = 20
MIN_CLASSIFICATION_ACCURACY: float = 0.95
V2_8_FROZEN_RECONSTRUCTION_HASH: str = "1f4d9dfe44cb16e1"
V2_8_FROZEN_FAILCASE_HASH:       str = "d83d81ab8417c022"


@dataclass(frozen=True)
class NCOutcome:
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


def _evaluate_ncs() -> tuple[tuple[NCOutcome, ...], float]:
    outs: list[NCOutcome] = []
    for nc in all_repro_ncs():
        got = classify_nc(nc)
        outs.append(NCOutcome(
            nc_id=nc.nc_id,
            expected_class=nc.expected_class,
            predicted_class=got,
            correct=(got == nc.expected_class),
        ))
    rate = (
        round(sum(1 for o in outs if o.correct) / len(outs), 6)
        if outs else 0.0
    )
    return tuple(outs), rate


@dataclass(frozen=True)
class V411Report:
    started_at: datetime
    finished_at: datetime
    environment: EnvironmentFingerprint
    tool_repro_policy: str
    expected_tool_correct_under_env: int
    v2_8_frozen_hash: str
    v2_8_live_hash: str | None
    v2_8_hash_equal: bool
    v2_8_repro_class: str
    matrix: tuple[MatrixEntry, ...]
    class_distribution: dict[str, int]
    nc_count: int
    nc_outcomes: tuple[NCOutcome, ...]
    classification_accuracy: float
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "environment": self.environment.to_dict(),
            "tool_repro_policy": self.tool_repro_policy,
            "expected_tool_correct_under_env":
                self.expected_tool_correct_under_env,
            "v2_8_frozen_hash": self.v2_8_frozen_hash,
            "v2_8_live_hash": self.v2_8_live_hash,
            "v2_8_hash_equal": self.v2_8_hash_equal,
            "v2_8_repro_class": self.v2_8_repro_class,
            "matrix": [e.to_dict() for e in self.matrix],
            "class_distribution":
                dict(self.class_distribution),
            "nc_count": self.nc_count,
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "classification_accuracy":
                self.classification_accuracy,
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in (
            "started_at", "finished_at", "replay_hash",
            "environment",  # exclude env so the hash is stable
        )
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _decide(
    *,
    classification_accuracy: float,
    nc_count: int,
    matrix: tuple[MatrixEntry, ...],
) -> tuple[str, str]:
    if nc_count < MIN_NC_COUNT:
        return (
            RecommendationOutcome.NONE.value,
            f"nc_count={nc_count} < {MIN_NC_COUNT}",
        )
    if classification_accuracy < MIN_CLASSIFICATION_ACCURACY:
        return (
            RecommendationOutcome.FAILED.value,
            (
                f"classification_accuracy="
                f"{classification_accuracy} < "
                f"{MIN_CLASSIFICATION_ACCURACY}"
            ),
        )
    unknown = sum(
        1 for e in matrix
        if e.repro_class == (
            ReproducibilityClass.UNKNOWN.value
        )
    )
    if unknown > 0:
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"{unknown} matrix entries classified as UNKNOWN"
            ),
        )
    drift = sum(
        1 for e in matrix
        if e.repro_class == (
            ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value
        )
    )
    if drift == 0:
        reason = (
            "all versions classified; no drift entries; "
            f"tool_repro_policy={TOOL_REPRO_POLICY.value}"
        )
        return RecommendationOutcome.CONFIRMED.value, reason
    # Drift classified explicitly is acceptable under v4.11
    # — the directive's CONFIRMED rule requires that drift be
    # *explicit*, not hidden, which is exactly what this
    # report records.
    reason = (
        f"{drift} entries classified as "
        "HISTORICAL_RUNTIME_DRIFT; drift is explicit, "
        "matrix entries are complete; "
        f"tool_repro_policy={TOOL_REPRO_POLICY.value}"
    )
    return RecommendationOutcome.CONFIRMED.value, reason


def build_v411_report(
    *, started_at: datetime, finished_at: datetime,
) -> V411Report:
    env = fingerprint()
    matrix = build_matrix()
    v28 = next(e for e in matrix if e.version == "v2_8")
    nc_outcomes, accuracy = _evaluate_ncs()
    distribution = dict(
        Counter(e.repro_class for e in matrix),
    )
    expected_tool = expected_correct_count(
        sympy_available=env.sympy_available,
    )
    recommendation, reason = _decide(
        classification_accuracy=accuracy,
        nc_count=len(nc_outcomes),
        matrix=matrix,
    )
    payload = {
        "tool_repro_policy": TOOL_REPRO_POLICY.value,
        "expected_tool_correct_under_env": expected_tool,
        "v2_8_frozen_hash": V2_8_FROZEN_RECONSTRUCTION_HASH,
        "v2_8_live_hash": v28.live_hash,
        "v2_8_hash_equal": bool(v28.hash_equal),
        "v2_8_repro_class": v28.repro_class,
        "matrix": [e.to_dict() for e in matrix],
        "class_distribution": distribution,
        "nc_count": len(nc_outcomes),
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "classification_accuracy": accuracy,
        "recommended_next": recommendation,
        "recommendation_reason": reason,
    }
    return V411Report(
        started_at=started_at, finished_at=finished_at,
        environment=env,
        tool_repro_policy=TOOL_REPRO_POLICY.value,
        expected_tool_correct_under_env=expected_tool,
        v2_8_frozen_hash=V2_8_FROZEN_RECONSTRUCTION_HASH,
        v2_8_live_hash=v28.live_hash,
        v2_8_hash_equal=bool(v28.hash_equal),
        v2_8_repro_class=v28.repro_class,
        matrix=matrix,
        class_distribution=distribution,
        nc_count=len(nc_outcomes),
        nc_outcomes=nc_outcomes,
        classification_accuracy=accuracy,
        recommended_next=recommendation,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "MIN_CLASSIFICATION_ACCURACY", "MIN_NC_COUNT",
    "NCOutcome", "V2_8_FROZEN_FAILCASE_HASH",
    "V2_8_FROZEN_RECONSTRUCTION_HASH",
    "V411Report", "build_v411_report",
]
