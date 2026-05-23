"""Aufgaben 10 + 11 — report build + recommendation gate."""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .contamination import ContaminationReport, check as contam_check
from .effect import EffectReport, measure as effect_measure
from .extensions import PATCHED_CLUSTERS, all_extensions
from .negative_controls import PatchNC, all_patch_ncs


# ----- Thresholds (Aufgabe 6 + 9 + 11) -------------------------

FALSE_SUPPORT_TARGET_AFTER: int = 24
FALSE_SUPPORT_BEFORE: int = 143
MIN_NC_DETECTION: float = 0.95
MIN_NC_COUNT: int = 80
V40_PRE_V43_REPLAY_HASH: str = "aefa8f1e3429225a"
V41_PRE_V43_REPLAY_HASH: str = "f7ec695f17aa341b"
V42_PRE_V43_REPLAY_HASH: str = "181ec3cb1febf62f"


class RecommendationOutcome(str, Enum):
    CONFIRMED = "EXTERNAL_AUDIT_PATCH_CONFIRMED"
    PARTIAL   = "EXTERNAL_AUDIT_PATCH_PARTIAL"
    FAILED    = "EXTERNAL_AUDIT_PATCH_FAILED"
    NONE      = "NONE"


# ----- NC scoring ---------------------------------------------

@dataclass(frozen=True)
class NCOutcome:
    nc_id: str
    target_class: str
    audit_state: str
    audit_rule: str | None
    detected: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "target_class": self.target_class,
            "audit_state": self.audit_state,
            "audit_rule": self.audit_rule,
            "detected": self.detected,
        }


def _evaluate_ncs() -> tuple[
    tuple[NCOutcome, ...], float, dict[str, dict[str, int]],
]:
    """A fixture is *detected* when the patched audit no longer
    returns ``LOGICALLY_SUPPORTED`` under ``CAUSAL_CHAIN`` —
    i.e., the patch caused the chain to suspend."""
    auditor = LogicalAuditor()
    out: list[NCOutcome] = []
    by_class: dict[str, dict[str, int]] = {}
    for nc in all_patch_ncs():
        a = auditor.audit(nc.text)
        detected = not (
            a.state is LogicalState.LOGICALLY_SUPPORTED
            and a.rule is InferenceRule.CAUSAL_CHAIN
        )
        out.append(NCOutcome(
            nc_id=nc.nc_id, target_class=nc.target_class,
            audit_state=a.state.value,
            audit_rule=a.rule.value if a.rule else None,
            detected=detected,
        ))
        slot = by_class.setdefault(
            nc.target_class, {"total": 0, "detected": 0},
        )
        slot["total"] += 1
        if detected:
            slot["detected"] += 1
    rate = (
        round(sum(1 for o in out if o.detected) / len(out), 6)
        if out else 0.0
    )
    return tuple(out), rate, by_class


# ----- Top-level report ---------------------------------------

@dataclass(frozen=True)
class V43Report:
    started_at: datetime
    finished_at: datetime
    extensions_per_class: dict[str, tuple[str, ...]]
    extension_token_count: int
    contamination: ContaminationReport
    effect: EffectReport
    nc_outcomes: tuple[NCOutcome, ...]
    nc_detection_rate: float
    nc_by_class: dict[str, dict[str, int]]
    nc_count: int
    v40_pre_v43_replay_hash: str
    v41_pre_v43_replay_hash: str
    v42_pre_v43_replay_hash: str
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "extensions_per_class": {
                k: list(v) for k, v in
                sorted(self.extensions_per_class.items())
            },
            "extension_token_count": self.extension_token_count,
            "contamination": self.contamination.to_dict(),
            "effect": self.effect.to_dict(),
            "nc_outcomes": [n.to_dict() for n in self.nc_outcomes],
            "nc_detection_rate": self.nc_detection_rate,
            "nc_by_class": {
                k: dict(v) for k, v in
                sorted(self.nc_by_class.items())
            },
            "nc_count": self.nc_count,
            "v40_pre_v43_replay_hash":
                self.v40_pre_v43_replay_hash,
            "v41_pre_v43_replay_hash":
                self.v41_pre_v43_replay_hash,
            "v42_pre_v43_replay_hash":
                self.v42_pre_v43_replay_hash,
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
    nc_count: int,
) -> tuple[str, str]:
    # FAILED: contamination or protected regression.
    if contamination.total_contamination > 0:
        return (
            RecommendationOutcome.FAILED.value,
            (
                f"contamination_count="
                f"{contamination.total_contamination} > 0"
            ),
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

    # CONFIRMED: all hard gates pass.
    confirmed = (
        effect.false_support_after <= FALSE_SUPPORT_TARGET_AFTER
        and contamination.total_contamination == 0
        and nc_detection_rate >= MIN_NC_DETECTION
    )
    if confirmed:
        return (
            RecommendationOutcome.CONFIRMED.value,
            (
                f"false_support_before="
                f"{effect.false_support_before} -> after="
                f"{effect.false_support_after} "
                f"(reduction={effect.false_support_reduction}, "
                f"rate={effect.reduction_rate}); "
                f"contamination=0; "
                f"nc_detection_rate={nc_detection_rate}"
            ),
        )

    # PARTIAL: false_support < before but > target.
    if (
        effect.false_support_after < effect.false_support_before
        and effect.false_support_after > FALSE_SUPPORT_TARGET_AFTER
        and contamination.total_contamination == 0
    ):
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"false_support_after="
                f"{effect.false_support_after} > target="
                f"{FALSE_SUPPORT_TARGET_AFTER}"
            ),
        )

    # CONFIRMED-thresholds-but-NC-rate-low edge case.
    if (
        effect.false_support_after <= FALSE_SUPPORT_TARGET_AFTER
        and contamination.total_contamination == 0
        and nc_detection_rate < MIN_NC_DETECTION
    ):
        return (
            RecommendationOutcome.PARTIAL.value,
            (
                f"false_support_after="
                f"{effect.false_support_after} <= "
                f"{FALSE_SUPPORT_TARGET_AFTER} but "
                f"nc_detection_rate={nc_detection_rate} < "
                f"{MIN_NC_DETECTION}"
            ),
        )

    return (
        RecommendationOutcome.NONE.value,
        "no rule fired",
    )


def build_v43_report(
    *, started_at: datetime, finished_at: datetime,
) -> V43Report:
    contamination = contam_check()
    effect = effect_measure()
    nc_outcomes, nc_rate, nc_by_class = _evaluate_ncs()
    extensions = all_extensions()
    token_count = sum(len(v) for v in extensions.values())
    recommendation, reason = _decide(
        effect=effect,
        contamination=contamination,
        nc_detection_rate=nc_rate,
        nc_count=len(nc_outcomes),
    )
    payload = {
        "extensions_per_class": {
            k: list(v) for k, v in extensions.items()
        },
        "extension_token_count": token_count,
        "contamination": contamination.to_dict(),
        "effect": effect.to_dict(),
        "nc_outcomes": [n.to_dict() for n in nc_outcomes],
        "nc_detection_rate": nc_rate,
        "nc_by_class": nc_by_class,
        "nc_count": len(nc_outcomes),
        "v40_pre_v43_replay_hash": V40_PRE_V43_REPLAY_HASH,
        "v41_pre_v43_replay_hash": V41_PRE_V43_REPLAY_HASH,
        "v42_pre_v43_replay_hash": V42_PRE_V43_REPLAY_HASH,
        "recommended_next": recommendation,
        "recommendation_reason": reason,
    }
    return V43Report(
        started_at=started_at, finished_at=finished_at,
        extensions_per_class=extensions,
        extension_token_count=token_count,
        contamination=contamination,
        effect=effect,
        nc_outcomes=nc_outcomes,
        nc_detection_rate=nc_rate,
        nc_by_class=nc_by_class,
        nc_count=len(nc_outcomes),
        v40_pre_v43_replay_hash=V40_PRE_V43_REPLAY_HASH,
        v41_pre_v43_replay_hash=V41_PRE_V43_REPLAY_HASH,
        v42_pre_v43_replay_hash=V42_PRE_V43_REPLAY_HASH,
        recommended_next=recommendation,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "FALSE_SUPPORT_BEFORE",
    "FALSE_SUPPORT_TARGET_AFTER",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "NCOutcome",
    "RecommendationOutcome",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43Report",
    "build_v43_report",
]
