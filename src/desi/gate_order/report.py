"""Aufgaben — report + recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import OrderingName, all_orderings
from .simulator import (
    ChainTrace, GateState, OrderMetrics,
    compute_states, run_ordering,
)


MIN_CHAIN_COUNT: int = 600
MIN_ATTACK_COUNT: int = 400
MIN_TRANSITION_COUNT: int = 2500

MIN_HELDOUT_RECALL: float = 0.85
MAX_VALID_BLOCK_RATE: float = 0.05


@dataclass(frozen=True)
class OrderingReport:
    metrics: OrderMetrics
    passes_hard_gates: bool
    fail_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics.to_dict(),
            "passes_hard_gates": self.passes_hard_gates,
            "fail_reasons": list(self.fail_reasons),
        }


def _hard_gate_failures(m: OrderMetrics,
                         baseline_attack_rate: float) -> tuple[str, ...]:
    reasons: list[str] = []
    if m.attack_success_rate > baseline_attack_rate:
        reasons.append(
            f"attack_success_rate={m.attack_success_rate} "
            f"> baseline={baseline_attack_rate}"
        )
    if m.heldout_recall < MIN_HELDOUT_RECALL:
        reasons.append(
            f"heldout_recall={m.heldout_recall} "
            f"< {MIN_HELDOUT_RECALL}"
        )
    if m.false_route_count != 0:
        reasons.append(
            f"false_route_count={m.false_route_count} != 0"
        )
    if m.contamination_count != 0:
        reasons.append(
            f"contamination_count={m.contamination_count} != 0"
        )
    if m.valid_block_rate > MAX_VALID_BLOCK_RATE:
        reasons.append(
            f"valid_block_rate={m.valid_block_rate} "
            f"> {MAX_VALID_BLOCK_RATE}"
        )
    return tuple(reasons)


@dataclass(frozen=True)
class GateOrderReport:
    started_at: datetime
    finished_at: datetime
    chain_count: int
    attack_count: int
    transition_count: int
    baseline_attack_success_rate: float
    orderings: tuple[OrderingReport, ...]
    best_ordering: str | None
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "chain_count": self.chain_count,
            "attack_count": self.attack_count,
            "transition_count": self.transition_count,
            "baseline_attack_success_rate":
                self.baseline_attack_success_rate,
            "orderings": [o.to_dict() for o in self.orderings],
            "best_ordering": self.best_ordering,
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


def _decide(
    *,
    chain_count: int, attack_count: int, transition_count: int,
    orderings: tuple[OrderingReport, ...],
    baseline_rate: float,
) -> tuple[str, str, str | None]:
    # Sanity gates for the audit itself.
    issues: list[str] = []
    if chain_count < MIN_CHAIN_COUNT:
        issues.append(
            f"chain_count={chain_count} < {MIN_CHAIN_COUNT}"
        )
    if attack_count < MIN_ATTACK_COUNT:
        issues.append(
            f"attack_count={attack_count} < {MIN_ATTACK_COUNT}"
        )
    if transition_count < MIN_TRANSITION_COUNT:
        issues.append(
            f"transition_count={transition_count} "
            f"< {MIN_TRANSITION_COUNT}"
        )

    # Filter to orderings that pass all hard gates.
    survivors = [
        o for o in orderings if o.passes_hard_gates
    ]
    # Among survivors, find the one with strictly LOWER
    # attack_success_rate than baseline. If multiple, prefer
    # lowest rate, then lowest valid_block_rate, then
    # alphabetical ordering.
    better = [
        o for o in survivors
        if o.metrics.attack_success_rate < baseline_rate
    ]
    better.sort(
        key=lambda o: (
            o.metrics.attack_success_rate,
            o.metrics.valid_block_rate,
            o.metrics.ordering,
        ),
    )
    best = better[0].metrics.ordering if better else None

    if issues:
        return "NONE", "; ".join(issues), None

    if best is None:
        return (
            "KEEP_CURRENT_ORDER",
            f"no ordering improves attack_success_rate "
            f"({baseline_rate}) without violating hard gates",
            None,
        )
    return (
        "GATE_STACK_REORDER",
        f"best ordering {best} beats baseline "
        f"{baseline_rate} on attack_success_rate without "
        "violating hard gates",
        best,
    )


def build_gate_order_report(
    *, started_at: datetime, finished_at: datetime,
) -> GateOrderReport:
    chains = all_chains()
    attack_count = sum(1 for c in chains if c.is_attack)
    transition_count = len(chains) * transitions_per_chain()

    states = compute_states(chains)

    per_ordering: list[OrderingReport] = []
    baseline_rate: float | None = None
    for name in all_orderings():
        metrics, _traces = run_ordering(name, chains, states)
        if name is OrderingName.CURRENT_ORDER:
            baseline_rate = metrics.attack_success_rate
        per_ordering.append(OrderingReport(
            metrics=metrics,
            passes_hard_gates=True,  # filled in below
            fail_reasons=(),
        ))

    assert baseline_rate is not None

    # Now evaluate hard gates with baseline known.
    evaluated: list[OrderingReport] = []
    for o in per_ordering:
        reasons = _hard_gate_failures(o.metrics, baseline_rate)
        evaluated.append(OrderingReport(
            metrics=o.metrics,
            passes_hard_gates=not reasons,
            fail_reasons=reasons,
        ))

    rec, reason, best = _decide(
        chain_count=len(chains),
        attack_count=attack_count,
        transition_count=transition_count,
        orderings=tuple(evaluated),
        baseline_rate=baseline_rate,
    )

    payload = {
        "chain_count": len(chains),
        "attack_count": attack_count,
        "transition_count": transition_count,
        "baseline_attack_success_rate": baseline_rate,
        "orderings": [o.to_dict() for o in evaluated],
        "best_ordering": best,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return GateOrderReport(
        started_at=started_at,
        finished_at=finished_at,
        chain_count=len(chains),
        attack_count=attack_count,
        transition_count=transition_count,
        baseline_attack_success_rate=baseline_rate,
        orderings=tuple(evaluated),
        best_ordering=best,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "GateOrderReport",
    "MAX_VALID_BLOCK_RATE",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_HELDOUT_RECALL",
    "MIN_TRANSITION_COUNT",
    "OrderingReport",
    "build_gate_order_report",
]
