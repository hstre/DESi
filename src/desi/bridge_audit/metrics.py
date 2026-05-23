"""Per-stage + per-category metrics — Aufgabe 4."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..benchmark_multistep.case import MultiStepCategory
from .loss_stage import LossStage
from .runner import BridgeAuditRun


@dataclass(frozen=True)
class FunnelCounts:
    """Counters from one full audit run."""

    parser_loss_count: int
    audit_reject_loss_count: int
    bridge_missing_loss_count: int
    consilium_veto_loss_count: int
    resolver_not_reached_count: int
    resolver_zero_depth_count: int
    cycle_not_recognized_count: int
    no_loss_count: int
    unknown_loss_count: int

    @property
    def total(self) -> int:
        return (
            self.parser_loss_count
            + self.audit_reject_loss_count
            + self.bridge_missing_loss_count
            + self.consilium_veto_loss_count
            + self.resolver_not_reached_count
            + self.resolver_zero_depth_count
            + self.cycle_not_recognized_count
            + self.no_loss_count
            + self.unknown_loss_count
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "parser_loss_count": self.parser_loss_count,
            "audit_reject_loss_count": self.audit_reject_loss_count,
            "bridge_missing_loss_count": self.bridge_missing_loss_count,
            "consilium_veto_loss_count": self.consilium_veto_loss_count,
            "resolver_not_reached_count": self.resolver_not_reached_count,
            "resolver_zero_depth_count": self.resolver_zero_depth_count,
            "cycle_not_recognized_count": self.cycle_not_recognized_count,
            "no_loss_count": self.no_loss_count,
            "unknown_loss_count": self.unknown_loss_count,
        }


def compute_funnel_counts(run: BridgeAuditRun) -> FunnelCounts:
    c: Counter[LossStage] = Counter(t.loss_stage for t in run.traces)
    return FunnelCounts(
        parser_loss_count=c.get(LossStage.PARSER_LOSS, 0),
        audit_reject_loss_count=c.get(LossStage.AUDIT_REJECT_LOSS, 0),
        bridge_missing_loss_count=c.get(LossStage.BRIDGE_MISSING_LOSS, 0),
        consilium_veto_loss_count=c.get(LossStage.CONSILIUM_VETO_LOSS, 0),
        resolver_not_reached_count=c.get(LossStage.RESOLVER_NOT_REACHED, 0),
        resolver_zero_depth_count=c.get(LossStage.RESOLVER_ZERO_DEPTH, 0),
        cycle_not_recognized_count=c.get(LossStage.CYCLE_NOT_RECOGNIZED, 0),
        no_loss_count=c.get(LossStage.NO_LOSS, 0),
        unknown_loss_count=c.get(LossStage.UNKNOWN_LOSS, 0),
    )


def compute_category_loss_distribution(
    run: BridgeAuditRun,
) -> dict[str, dict[str, int]]:
    """Map ``category → loss_stage → count``."""
    case_id_to_category = {
        c.case_id: c.category for c in ALL_MULTISTEP_CASES
    }
    out: dict[str, dict[str, int]] = {}
    for cat in MultiStepCategory:
        out[cat.value] = {ls.value: 0 for ls in LossStage}
    for t in run.traces:
        cat = case_id_to_category.get(t.case_id)
        if cat is None:
            continue
        out[cat.value][t.loss_stage.value] += 1
    return out


def dominant_loss_stage(counts: FunnelCounts) -> LossStage:
    """The single most frequent non-NO_LOSS stage.

    Deterministic tie-break: enum declaration order.
    """
    table: list[tuple[LossStage, int]] = [
        (LossStage.PARSER_LOSS, counts.parser_loss_count),
        (LossStage.AUDIT_REJECT_LOSS, counts.audit_reject_loss_count),
        (LossStage.BRIDGE_MISSING_LOSS, counts.bridge_missing_loss_count),
        (LossStage.CONSILIUM_VETO_LOSS, counts.consilium_veto_loss_count),
        (LossStage.RESOLVER_NOT_REACHED, counts.resolver_not_reached_count),
        (LossStage.RESOLVER_ZERO_DEPTH, counts.resolver_zero_depth_count),
        (LossStage.CYCLE_NOT_RECOGNIZED, counts.cycle_not_recognized_count),
        (LossStage.UNKNOWN_LOSS, counts.unknown_loss_count),
    ]
    best = max(table, key=lambda kv: kv[1])
    if best[1] == 0:
        return LossStage.NO_LOSS
    return best[0]


__all__ = [
    "FunnelCounts",
    "compute_category_loss_distribution",
    "compute_funnel_counts",
    "dominant_loss_stage",
]
