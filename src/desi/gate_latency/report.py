"""Aufgaben 6 + 7 + 10 + 11 — safety + efficiency + recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..gate_order import compute_states
from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import EfficiencyClass, StackName, all_stacks
from .negative_control import (
    ALL_NCS, classify_delta, run_negative_controls,
)
from .simulator import StackMetrics, run_stack


MIN_CHAIN_COUNT: int = 600
MIN_ATTACK_COUNT: int = 400
MIN_TRANSITION_COUNT: int = 3000
MIN_NC_ACCURACY: float = 0.95


@dataclass(frozen=True)
class StackEvaluation:
    metrics: StackMetrics
    latency_delta: float
    efficiency: str
    is_safety_valid: bool
    safety_violations: tuple[str, ...]
    deltas: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics.to_dict(),
            "latency_delta": self.latency_delta,
            "efficiency": self.efficiency,
            "is_safety_valid": self.is_safety_valid,
            "safety_violations": list(self.safety_violations),
            "deltas": dict(self.deltas),
        }


def _safety_violations(
    metrics: StackMetrics, baseline: StackMetrics,
) -> tuple[str, ...]:
    out: list[str] = []
    if metrics.attack_success_rate > baseline.attack_success_rate:
        out.append(
            f"attack_success_rate={metrics.attack_success_rate} "
            f"> baseline={baseline.attack_success_rate}"
        )
    if metrics.heldout_recall < baseline.heldout_recall:
        out.append(
            f"heldout_recall={metrics.heldout_recall} "
            f"< baseline={baseline.heldout_recall}"
        )
    if metrics.false_route_count > baseline.false_route_count:
        out.append(
            f"false_route_count={metrics.false_route_count} "
            f"> baseline={baseline.false_route_count}"
        )
    if metrics.contamination_count != 0:
        out.append(
            f"contamination_count="
            f"{metrics.contamination_count} != 0"
        )
    return tuple(out)


def _deltas(
    metrics: StackMetrics, baseline: StackMetrics,
) -> dict[str, float]:
    bd = baseline.to_dict()
    md = metrics.to_dict()
    out: dict[str, float] = {}
    for k in ("attack_success_rate", "heldout_recall",
              "false_route_count", "contamination_count",
              "average_gate_depth", "gate_calls_total",
              "tool_calls_saved", "audit_calls_saved",
              "consilium_calls_saved", "routing_calls_saved",
              "latency_cost"):
        out[k] = round(float(md[k]) - float(bd[k]), 6)
    return out


def _latency_delta_pct(
    metrics: StackMetrics, baseline: StackMetrics,
) -> float:
    if baseline.latency_cost <= 0:
        return 0.0
    return round(
        (baseline.latency_cost - metrics.latency_cost)
        / baseline.latency_cost, 6,
    )


@dataclass(frozen=True)
class GateLatencyReport:
    started_at: datetime
    finished_at: datetime
    chain_count: int
    attack_count: int
    transition_count: int
    baseline: StackMetrics
    evaluations: tuple[StackEvaluation, ...]
    best_stack: str | None
    nc_accuracy: float
    nc_per_shape: dict[str, dict[str, int]]
    nc_outcomes: tuple[tuple[str, str, str, bool], ...]
    contamination_count: int
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
            "baseline": self.baseline.to_dict(),
            "evaluations":
                [e.to_dict() for e in self.evaluations],
            "best_stack": self.best_stack,
            "nc_accuracy": self.nc_accuracy,
            "nc_per_shape": dict(self.nc_per_shape),
            "nc_outcomes": [
                {
                    "case_id": c[0], "shape": c[1],
                    "observed": c[2], "correct": c[3],
                }
                for c in self.nc_outcomes
            ],
            "contamination_count": self.contamination_count,
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
    nc_acc: float, contamination: int,
    evaluations: tuple[StackEvaluation, ...],
) -> tuple[str, str, str | None]:
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
    if nc_acc < MIN_NC_ACCURACY:
        issues.append(
            f"nc_accuracy={nc_acc} < {MIN_NC_ACCURACY}"
        )
    if contamination != 0:
        issues.append(
            f"contamination_count={contamination} != 0"
        )

    if issues:
        return "NONE", "; ".join(issues), None

    # Find safety-valid stacks with at least SIGNIFICANT_GAIN.
    candidates = [
        e for e in evaluations
        if e.is_safety_valid
        and e.efficiency in (
            EfficiencyClass.SIGNIFICANT_GAIN.value,
            EfficiencyClass.MAJOR_GAIN.value,
        )
    ]
    candidates.sort(
        key=lambda e: (-e.latency_delta, e.metrics.stack),
    )
    if not candidates:
        return (
            "KEEP_CURRENT_STACK",
            "no stack reaches SIGNIFICANT_GAIN without safety "
            "violations",
            None,
        )
    chosen = candidates[0]
    return (
        "LATENCY_OPTIMIZED_STACK",
        f"best stack {chosen.metrics.stack} "
        f"(latency_delta={chosen.latency_delta}, "
        f"{chosen.efficiency}) passes all safety gates",
        chosen.metrics.stack,
    )


def build_gate_latency_report(
    *, started_at: datetime, finished_at: datetime,
) -> GateLatencyReport:
    chains = all_chains()
    attack_count = sum(1 for c in chains if c.is_attack)
    transition_count = len(chains) * transitions_per_chain()

    states = compute_states(chains)

    # Baseline first.
    baseline, _b_traces = run_stack(
        StackName.S1_CURRENT_ORDER, chains, states,
    )

    evaluations: list[StackEvaluation] = []
    for name in all_stacks():
        metrics, _traces = run_stack(name, chains, states)
        viol = _safety_violations(metrics, baseline)
        delta = _latency_delta_pct(metrics, baseline)
        evaluations.append(StackEvaluation(
            metrics=metrics,
            latency_delta=delta,
            efficiency=classify_delta(max(0.0, delta)).value,
            is_safety_valid=not viol,
            safety_violations=viol,
            deltas=_deltas(metrics, baseline),
        ))

    nc_outs, nc_acc, nc_per_shape = run_negative_controls()

    rec, reason, best = _decide(
        chain_count=len(chains),
        attack_count=attack_count,
        transition_count=transition_count,
        nc_acc=nc_acc,
        contamination=baseline.contamination_count,
        evaluations=tuple(evaluations),
    )

    payload = {
        "chain_count": len(chains),
        "attack_count": attack_count,
        "transition_count": transition_count,
        "baseline": baseline.to_dict(),
        "evaluations": [e.to_dict() for e in evaluations],
        "best_stack": best,
        "nc_accuracy": nc_acc,
        "nc_per_shape": nc_per_shape,
        "nc_outcomes": [
            {
                "case_id": c[0], "shape": c[1],
                "observed": c[2], "correct": c[3],
            }
            for c in nc_outs
        ],
        "contamination_count": baseline.contamination_count,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return GateLatencyReport(
        started_at=started_at,
        finished_at=finished_at,
        chain_count=len(chains),
        attack_count=attack_count,
        transition_count=transition_count,
        baseline=baseline,
        evaluations=tuple(evaluations),
        best_stack=best,
        nc_accuracy=nc_acc,
        nc_per_shape=nc_per_shape,
        nc_outcomes=nc_outs,
        contamination_count=baseline.contamination_count,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "GateLatencyReport",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "StackEvaluation",
    "build_gate_latency_report",
]
