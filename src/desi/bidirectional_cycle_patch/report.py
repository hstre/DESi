"""Aufgaben 8 + 12 — report assembly + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .contamination import ContaminationReport, check as contam_check
from .effect import EffectReport, measure as effect_measure
from .negative_controls import all_structural_ncs
from .structural_check import (
    MIN_OVERLAP_PREMISES, MIN_OVERLAP_TOTAL,
    fires_on_text,
)


TARGET_CLUSTER:        str  = "BIDIRECTIONAL_CYCLE"
TARGET_BEFORE_COUNT:   int  = 24
TARGET_AFTER_COUNT:    int  = 19
EXPECTED_REDUCTION:    int  = 5
MIN_NC_COUNT:          int  = 50
MIN_NC_DETECTION:      float = 0.95
MAX_FALSE_CYCLE_RATE:  float = 0.05
V40_PRE_V43_REPLAY_HASH: str = "aefa8f1e3429225a"
V41_PRE_V43_REPLAY_HASH: str = "f7ec695f17aa341b"
V42_PRE_V43_REPLAY_HASH: str = "181ec3cb1febf62f"
V43_REPLAY_HASH:         str = "7c63bcae4cf3fb37"
V44_REPLAY_HASH:         str = "bf4147b89f398224"


class RecommendationOutcome(str, Enum):
    CONFIRMED = "BIDIRECTIONAL_CYCLE_PATCH_CONFIRMED"
    PARTIAL   = "BIDIRECTIONAL_CYCLE_PATCH_PARTIAL"
    FAILED    = "BIDIRECTIONAL_CYCLE_PATCH_FAILED"
    NONE      = "NONE"


# ---- NC scoring ---------------------------------------------

@dataclass(frozen=True)
class NCOutcome:
    nc_id: str
    is_cycle: bool
    fired: bool
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "is_cycle": self.is_cycle,
            "fired": self.fired,
            "correct": self.correct,
        }


def _evaluate_ncs() -> tuple[
    tuple[NCOutcome, ...], float, float,
]:
    """Returns (per-NC outcomes, nc_detection_rate,
    false_cycle_rate)."""
    ncs = all_structural_ncs()
    out: list[NCOutcome] = []
    cycle_total = 0
    cycle_detected = 0
    non_cycle_total = 0
    non_cycle_false = 0
    for nc in ncs:
        fired = fires_on_text(nc.text)
        correct = fired == nc.is_cycle
        out.append(NCOutcome(
            nc_id=nc.nc_id, is_cycle=nc.is_cycle,
            fired=fired, correct=correct,
        ))
        if nc.is_cycle:
            cycle_total += 1
            if fired:
                cycle_detected += 1
        else:
            non_cycle_total += 1
            if fired:
                non_cycle_false += 1
    detection = (
        round(cycle_detected / cycle_total, 6)
        if cycle_total else 0.0
    )
    false_cycle = (
        round(non_cycle_false / non_cycle_total, 6)
        if non_cycle_total else 0.0
    )
    return tuple(out), detection, false_cycle


# ---- top-level report ---------------------------------------

@dataclass(frozen=True)
class V45Report:
    started_at: datetime
    finished_at: datetime
    target_cluster: str
    min_overlap_premises: int
    min_overlap_total: int
    effect: EffectReport
    contamination: ContaminationReport
    nc_outcomes: tuple[NCOutcome, ...]
    nc_detection_rate: float
    false_cycle_rate: float
    nc_count: int
    v40_pre_v43_replay_hash: str
    v41_pre_v43_replay_hash: str
    v42_pre_v43_replay_hash: str
    v43_replay_hash: str
    v44_replay_hash: str
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "target_cluster": self.target_cluster,
            "min_overlap_premises":
                self.min_overlap_premises,
            "min_overlap_total": self.min_overlap_total,
            "effect": self.effect.to_dict(),
            "contamination": self.contamination.to_dict(),
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "nc_detection_rate": self.nc_detection_rate,
            "false_cycle_rate": self.false_cycle_rate,
            "nc_count": self.nc_count,
            "v40_pre_v43_replay_hash":
                self.v40_pre_v43_replay_hash,
            "v41_pre_v43_replay_hash":
                self.v41_pre_v43_replay_hash,
            "v42_pre_v43_replay_hash":
                self.v42_pre_v43_replay_hash,
            "v43_replay_hash": self.v43_replay_hash,
            "v44_replay_hash": self.v44_replay_hash,
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
        cleaned, sort_keys=True, separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _decide(
    *,
    effect: EffectReport,
    contamination: ContaminationReport,
    nc_detection_rate: float,
    false_cycle_rate: float,
    nc_count: int,
) -> tuple[str, str]:
    # FAILED first.
    if contamination.contamination_count > 0:
        return (
            RecommendationOutcome.FAILED.value,
            f"contamination_count="
            f"{contamination.contamination_count} > 0",
        )
    if effect.non_target_relabel_count > 0:
        return (
            RecommendationOutcome.FAILED.value,
            (
                f"non_target_relabel_count="
                f"{effect.non_target_relabel_count} > 0 — "
                "non-target classes silently relabeled"
            ),
        )
    if nc_count < MIN_NC_COUNT:
        return (
            RecommendationOutcome.NONE.value,
            f"nc_count={nc_count} < {MIN_NC_COUNT}",
        )

    confirmed = (
        effect.false_support_after == TARGET_AFTER_COUNT
        and contamination.contamination_count == 0
        and nc_detection_rate >= MIN_NC_DETECTION
        and false_cycle_rate <= MAX_FALSE_CYCLE_RATE
    )
    if confirmed:
        return (
            RecommendationOutcome.CONFIRMED.value,
            (
                f"false_support_before="
                f"{effect.false_support_before} -> after="
                f"{effect.false_support_after} "
                f"(reduction={effect.reduction}); "
                f"contamination=0; "
                f"nc_detection_rate={nc_detection_rate}; "
                f"false_cycle_rate={false_cycle_rate}"
            ),
        )

    # PARTIAL: reduced below before but didn't hit target.
    if (
        effect.false_support_after < effect.false_support_before
        and effect.false_support_after != TARGET_AFTER_COUNT
        and contamination.contamination_count == 0
    ):
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"false_support_after="
                f"{effect.false_support_after} != target="
                f"{TARGET_AFTER_COUNT}"
            ),
        )

    # Edge: target hit but NC thresholds miss.
    if (
        effect.false_support_after == TARGET_AFTER_COUNT
        and (
            nc_detection_rate < MIN_NC_DETECTION
            or false_cycle_rate > MAX_FALSE_CYCLE_RATE
        )
    ):
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"target hit but nc_detection_rate="
                f"{nc_detection_rate} / false_cycle_rate="
                f"{false_cycle_rate}"
            ),
        )

    return (
        RecommendationOutcome.NONE.value,
        "no rule fired",
    )


def build_v45_report(
    *, started_at: datetime, finished_at: datetime,
) -> V45Report:
    effect = effect_measure(TARGET_CLUSTER)
    contamination = contam_check()
    nc_outcomes, nc_rate, false_cycle = _evaluate_ncs()
    recommendation, reason = _decide(
        effect=effect, contamination=contamination,
        nc_detection_rate=nc_rate,
        false_cycle_rate=false_cycle,
        nc_count=len(nc_outcomes),
    )
    payload = {
        "target_cluster": TARGET_CLUSTER,
        "min_overlap_premises": MIN_OVERLAP_PREMISES,
        "min_overlap_total": MIN_OVERLAP_TOTAL,
        "effect": effect.to_dict(),
        "contamination": contamination.to_dict(),
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "nc_detection_rate": nc_rate,
        "false_cycle_rate": false_cycle,
        "nc_count": len(nc_outcomes),
        "v40_pre_v43_replay_hash": V40_PRE_V43_REPLAY_HASH,
        "v41_pre_v43_replay_hash": V41_PRE_V43_REPLAY_HASH,
        "v42_pre_v43_replay_hash": V42_PRE_V43_REPLAY_HASH,
        "v43_replay_hash": V43_REPLAY_HASH,
        "v44_replay_hash": V44_REPLAY_HASH,
        "recommended_next": recommendation,
        "recommendation_reason": reason,
    }
    return V45Report(
        started_at=started_at, finished_at=finished_at,
        target_cluster=TARGET_CLUSTER,
        min_overlap_premises=MIN_OVERLAP_PREMISES,
        min_overlap_total=MIN_OVERLAP_TOTAL,
        effect=effect, contamination=contamination,
        nc_outcomes=nc_outcomes,
        nc_detection_rate=nc_rate,
        false_cycle_rate=false_cycle,
        nc_count=len(nc_outcomes),
        v40_pre_v43_replay_hash=V40_PRE_V43_REPLAY_HASH,
        v41_pre_v43_replay_hash=V41_PRE_V43_REPLAY_HASH,
        v42_pre_v43_replay_hash=V42_PRE_V43_REPLAY_HASH,
        v43_replay_hash=V43_REPLAY_HASH,
        v44_replay_hash=V44_REPLAY_HASH,
        recommended_next=recommendation,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "EXPECTED_REDUCTION",
    "MAX_FALSE_CYCLE_RATE",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "NCOutcome",
    "RecommendationOutcome",
    "TARGET_AFTER_COUNT",
    "TARGET_BEFORE_COUNT",
    "TARGET_CLUSTER",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH",
    "V44_REPLAY_HASH",
    "V45Report",
    "build_v45_report",
]
