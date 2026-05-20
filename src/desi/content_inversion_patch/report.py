"""Aufgaben 8 + 12 — report + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .contamination import (
    ContaminationReport, check as contam_check,
)
from .effect import (
    EffectReport, TARGET_CLUSTERS, measure as effect_measure,
)
from .inversion_check import (
    CONTRADICTION_PAIRS, POLARITY_PAIRS, any_inversion_fires,
)
from .negative_controls import all_inversion_ncs


TARGET_BEFORE_COUNT:   int   = 9
TARGET_AFTER_COUNT:    int   = 0
EXPECTED_REDUCTION:    int   = 9
MIN_NC_COUNT:          int   = 60
MIN_NC_DETECTION:      float = 0.95
MAX_FALSE_INVERSION:   float = 0.05
V40_PRE_V43_REPLAY_HASH: str = "aefa8f1e3429225a"
V41_PRE_V43_REPLAY_HASH: str = "f7ec695f17aa341b"
V42_PRE_V43_REPLAY_HASH: str = "181ec3cb1febf62f"
V43_REPLAY_HASH:         str = "7c63bcae4cf3fb37"
V44_REPLAY_HASH:         str = "bf4147b89f398224"
V45_REPLAY_HASH:         str = "86418c9d976cc147"
V46_REPLAY_HASH:         str = "58268fd9c4437e49"
V47_REPLAY_HASH:         str = "2774818766a8035a"
V48_REPLAY_HASH:         str = "d0835b564453cfc0"


class RecommendationOutcome(str, Enum):
    CONFIRMED = "CONTENT_INVERSION_PATCH_CONFIRMED"
    PARTIAL   = "CONTENT_INVERSION_PATCH_PARTIAL"
    FAILED    = "CONTENT_INVERSION_PATCH_FAILED"
    NONE      = "NONE"


@dataclass(frozen=True)
class NCOutcome:
    nc_id: str
    cohort: str
    is_inversion: bool
    fired: bool
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "cohort": self.cohort,
            "is_inversion": self.is_inversion,
            "fired": self.fired,
            "correct": self.correct,
        }


def _evaluate_ncs() -> tuple[
    tuple[NCOutcome, ...], float, float,
]:
    ncs = all_inversion_ncs()
    out: list[NCOutcome] = []
    inv_total = 0
    inv_caught = 0
    cp_total = 0
    cp_false = 0
    for nc in ncs:
        fired = any_inversion_fires(nc.text)
        correct = fired == nc.is_inversion
        out.append(NCOutcome(
            nc_id=nc.nc_id, cohort=nc.cohort,
            is_inversion=nc.is_inversion,
            fired=fired, correct=correct,
        ))
        if nc.is_inversion:
            inv_total += 1
            if fired:
                inv_caught += 1
        else:
            cp_total += 1
            if fired:
                cp_false += 1
    detection = (
        round(inv_caught / inv_total, 6) if inv_total else 0.0
    )
    false_inv = (
        round(cp_false / cp_total, 6) if cp_total else 0.0
    )
    return tuple(out), detection, false_inv


@dataclass(frozen=True)
class V49Report:
    started_at: datetime
    finished_at: datetime
    target_clusters: tuple[str, ...]
    contradiction_pair_count: int
    polarity_pair_count: int
    effect: EffectReport
    contamination: ContaminationReport
    nc_outcomes: tuple[NCOutcome, ...]
    nc_detection_rate: float
    false_inversion_rate: float
    nc_count: int
    v40_pre_v43_replay_hash: str
    v41_pre_v43_replay_hash: str
    v42_pre_v43_replay_hash: str
    v43_replay_hash: str
    v44_replay_hash: str
    v45_replay_hash: str
    v46_replay_hash: str
    v47_replay_hash: str
    v48_replay_hash: str
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "target_clusters": list(self.target_clusters),
            "contradiction_pair_count":
                self.contradiction_pair_count,
            "polarity_pair_count":
                self.polarity_pair_count,
            "effect": self.effect.to_dict(),
            "contamination": self.contamination.to_dict(),
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "nc_detection_rate": self.nc_detection_rate,
            "false_inversion_rate": self.false_inversion_rate,
            "nc_count": self.nc_count,
            "v40_pre_v43_replay_hash":
                self.v40_pre_v43_replay_hash,
            "v41_pre_v43_replay_hash":
                self.v41_pre_v43_replay_hash,
            "v42_pre_v43_replay_hash":
                self.v42_pre_v43_replay_hash,
            "v43_replay_hash": self.v43_replay_hash,
            "v44_replay_hash": self.v44_replay_hash,
            "v45_replay_hash": self.v45_replay_hash,
            "v46_replay_hash": self.v46_replay_hash,
            "v47_replay_hash": self.v47_replay_hash,
            "v48_replay_hash": self.v48_replay_hash,
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
    false_inversion_rate: float,
    nc_count: int,
) -> tuple[str, str]:
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
                f"{effect.non_target_relabel_count} > 0"
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
        and false_inversion_rate <= MAX_FALSE_INVERSION
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
                f"false_inversion_rate={false_inversion_rate}"
            ),
        )

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

    if (
        effect.false_support_after == TARGET_AFTER_COUNT
        and (
            nc_detection_rate < MIN_NC_DETECTION
            or false_inversion_rate > MAX_FALSE_INVERSION
        )
    ):
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"target hit but nc_detection_rate="
                f"{nc_detection_rate} / false_inversion_rate="
                f"{false_inversion_rate}"
            ),
        )

    return RecommendationOutcome.NONE.value, "no rule fired"


def build_v49_report(
    *, started_at: datetime, finished_at: datetime,
) -> V49Report:
    effect = effect_measure()
    contamination = contam_check()
    nc_outcomes, nc_rate, false_inv = _evaluate_ncs()
    recommendation, reason = _decide(
        effect=effect, contamination=contamination,
        nc_detection_rate=nc_rate,
        false_inversion_rate=false_inv,
        nc_count=len(nc_outcomes),
    )
    payload = {
        "target_clusters": list(TARGET_CLUSTERS),
        "contradiction_pair_count": len(CONTRADICTION_PAIRS),
        "polarity_pair_count": len(POLARITY_PAIRS),
        "effect": effect.to_dict(),
        "contamination": contamination.to_dict(),
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "nc_detection_rate": nc_rate,
        "false_inversion_rate": false_inv,
        "nc_count": len(nc_outcomes),
        "v40_pre_v43_replay_hash": V40_PRE_V43_REPLAY_HASH,
        "v41_pre_v43_replay_hash": V41_PRE_V43_REPLAY_HASH,
        "v42_pre_v43_replay_hash": V42_PRE_V43_REPLAY_HASH,
        "v43_replay_hash": V43_REPLAY_HASH,
        "v44_replay_hash": V44_REPLAY_HASH,
        "v45_replay_hash": V45_REPLAY_HASH,
        "v46_replay_hash": V46_REPLAY_HASH,
        "v47_replay_hash": V47_REPLAY_HASH,
        "v48_replay_hash": V48_REPLAY_HASH,
        "recommended_next": recommendation,
        "recommendation_reason": reason,
    }
    return V49Report(
        started_at=started_at, finished_at=finished_at,
        target_clusters=TARGET_CLUSTERS,
        contradiction_pair_count=len(CONTRADICTION_PAIRS),
        polarity_pair_count=len(POLARITY_PAIRS),
        effect=effect, contamination=contamination,
        nc_outcomes=nc_outcomes,
        nc_detection_rate=nc_rate,
        false_inversion_rate=false_inv,
        nc_count=len(nc_outcomes),
        v40_pre_v43_replay_hash=V40_PRE_V43_REPLAY_HASH,
        v41_pre_v43_replay_hash=V41_PRE_V43_REPLAY_HASH,
        v42_pre_v43_replay_hash=V42_PRE_V43_REPLAY_HASH,
        v43_replay_hash=V43_REPLAY_HASH,
        v44_replay_hash=V44_REPLAY_HASH,
        v45_replay_hash=V45_REPLAY_HASH,
        v46_replay_hash=V46_REPLAY_HASH,
        v47_replay_hash=V47_REPLAY_HASH,
        v48_replay_hash=V48_REPLAY_HASH,
        recommended_next=recommendation,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "EXPECTED_REDUCTION", "MAX_FALSE_INVERSION",
    "MIN_NC_COUNT", "MIN_NC_DETECTION",
    "NCOutcome", "RecommendationOutcome",
    "TARGET_AFTER_COUNT", "TARGET_BEFORE_COUNT",
    "V40_PRE_V43_REPLAY_HASH", "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH", "V43_REPLAY_HASH",
    "V44_REPLAY_HASH", "V45_REPLAY_HASH",
    "V46_REPLAY_HASH", "V47_REPLAY_HASH",
    "V48_REPLAY_HASH",
    "V49Report", "build_v49_report",
]
