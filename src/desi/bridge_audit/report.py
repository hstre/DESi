"""BridgeFunnelReport — Aufgabe 5.

Deterministic replay hash over the per-trace observables + the
loss-distribution counters. Two runs must produce byte-identical
``replay_hash`` values.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .loss_stage import LossStage
from .metrics import (
    FunnelCounts,
    compute_category_loss_distribution,
    compute_funnel_counts,
    dominant_loss_stage,
)
from .runner import BridgeAuditRun
from .trace import BridgeEntryTrace


@dataclass(frozen=True)
class BridgeFunnelReport:
    started_at: datetime
    finished_at: datetime
    total_cases: int
    loss_distribution: dict[str, int]
    category_loss_distribution: dict[str, dict[str, int]]
    dominant_loss_stage: LossStage
    recursion_reach_rate: float
    bridge_creation_rate: float
    consilium_call_rate: float
    resolver_entry_rate: float
    traces: tuple[BridgeEntryTrace, ...] = field(default_factory=tuple)
    replay_hash: str = ""
    reflection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_cases": self.total_cases,
            "loss_distribution": dict(self.loss_distribution),
            "category_loss_distribution": {
                k: dict(v)
                for k, v in self.category_loss_distribution.items()
            },
            "dominant_loss_stage": self.dominant_loss_stage.value,
            "recursion_reach_rate": self.recursion_reach_rate,
            "bridge_creation_rate": self.bridge_creation_rate,
            "consilium_call_rate": self.consilium_call_rate,
            "resolver_entry_rate": self.resolver_entry_rate,
            "traces": [t.to_dict() for t in self.traces],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_funnel_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_funnel_report(
    run: BridgeAuditRun,
    *,
    started_at: datetime,
    finished_at: datetime,
) -> BridgeFunnelReport:
    counts: FunnelCounts = compute_funnel_counts(run)
    cat_dist = compute_category_loss_distribution(run)
    total = len(run.traces)

    recursion_reach = sum(1 for t in run.traces if t.depth_reached > 0)
    bridge_created = sum(1 for t in run.traces if t.bridge_created)
    consilium_called = sum(1 for t in run.traces if t.consilium_called)
    resolver_entered = sum(1 for t in run.traces if t.resolver_entered)

    payload = {
        "total_cases": total,
        "loss_distribution": counts.to_dict(),
        "category_loss_distribution": cat_dist,
        "dominant_loss_stage": dominant_loss_stage(counts).value,
        "recursion_reach_rate": _ratio(recursion_reach, total),
        "bridge_creation_rate": _ratio(bridge_created, total),
        "consilium_call_rate": _ratio(consilium_called, total),
        "resolver_entry_rate": _ratio(resolver_entered, total),
        "traces": [t.to_dict() for t in run.traces],
    }
    replay_hash = compute_funnel_replay_hash(payload)

    return BridgeFunnelReport(
        started_at=started_at,
        finished_at=finished_at,
        total_cases=total,
        loss_distribution=counts.to_dict(),
        category_loss_distribution=cat_dist,
        dominant_loss_stage=dominant_loss_stage(counts),
        recursion_reach_rate=_ratio(recursion_reach, total),
        bridge_creation_rate=_ratio(bridge_created, total),
        consilium_call_rate=_ratio(consilium_called, total),
        resolver_entry_rate=_ratio(resolver_entered, total),
        traces=run.traces,
        replay_hash=replay_hash,
    )


__all__ = [
    "BridgeFunnelReport",
    "build_funnel_report",
    "compute_funnel_replay_hash",
]
