"""Aufgaben 6 + 9 + 10 — classification + recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import Gate, GateClassification, ablated_gates
from .negative_control import ALL_NCS, NCCase
from .simulator import (
    AblationMetrics, ChainOutcome,
    run_ablation, run_baseline,
)


DEAD_KNOB_DELTA: float = 0.05
PRIMARY_CLIFF_DELTA: float = 0.50

MIN_CHAIN_COUNT: int = 600
MIN_ATTACK_COUNT: int = 100
MIN_TRANSITION_COUNT: int = 2500
MIN_NC_ACCURACY: float = 0.95


def _max_delta(
    baseline: AblationMetrics, masked: AblationMetrics,
) -> float:
    bt = baseline.feature_tuple()
    mt = masked.feature_tuple()
    return max(abs(b - m) for b, m in zip(bt, mt))


def _classify(max_delta: float) -> GateClassification:
    if max_delta < DEAD_KNOB_DELTA:
        return GateClassification.DEAD_KNOB
    if max_delta > PRIMARY_CLIFF_DELTA:
        return GateClassification.PRIMARY_CLIFF
    return GateClassification.SUPPORT_LAYER


@dataclass(frozen=True)
class GateAblation:
    gate: str
    baseline: AblationMetrics
    masked: AblationMetrics
    deltas: dict[str, float]
    max_delta: float
    classification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "baseline": self.baseline.to_dict(),
            "masked": self.masked.to_dict(),
            "deltas": dict(self.deltas),
            "max_delta": self.max_delta,
            "classification": self.classification,
        }


def _deltas(
    baseline: AblationMetrics, masked: AblationMetrics,
) -> dict[str, float]:
    bd = baseline.to_dict()
    md = masked.to_dict()
    names = (
        "attack_success_rate", "heldout_recall",
        "false_positive_count", "contamination_count",
        "trajectory_separability", "routing_integrity",
        "manipulation_absorption",
    )
    return {
        n: round(abs(float(bd[n]) - float(md[n])), 6)
        for n in names
    }


@dataclass(frozen=True)
class NCOutcome:
    case_id: str
    shape: str
    expected: str
    observed: str
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id, "shape": self.shape,
            "expected": self.expected, "observed": self.observed,
            "correct": self.correct,
        }


def _run_nc() -> tuple[float, dict[str, dict[str, int]], tuple[NCOutcome, ...]]:
    per_shape: dict[str, dict[str, int]] = {}
    out: list[NCOutcome] = []
    correct_total = 0
    for nc in ALL_NCS:
        delta = _max_delta(nc.baseline_metrics, nc.masked_metrics)
        obs = _classify(delta)
        correct = obs is nc.expected_classification
        out.append(NCOutcome(
            case_id=nc.case_id, shape=nc.shape.value,
            expected=nc.expected_classification.value,
            observed=obs.value, correct=correct,
        ))
        b = per_shape.setdefault(
            nc.shape.value, {"total": 0, "correct": 0},
        )
        b["total"] += 1
        if correct:
            b["correct"] += 1
            correct_total += 1
    acc = round(correct_total / len(ALL_NCS), 6) if ALL_NCS else 0.0
    return acc, per_shape, tuple(out)


@dataclass(frozen=True)
class GateAblationReport:
    started_at: datetime
    finished_at: datetime
    chain_count: int
    attack_count: int
    transition_count: int
    baseline: AblationMetrics
    ablations: tuple[GateAblation, ...]
    primary_cliffs: tuple[str, ...]
    dead_knobs: tuple[str, ...]
    support_layers: tuple[str, ...]
    nc_accuracy: float
    nc_per_shape: dict[str, dict[str, int]]
    nc_outcomes: tuple[NCOutcome, ...]
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
            "ablations": [a.to_dict() for a in self.ablations],
            "primary_cliffs": list(self.primary_cliffs),
            "dead_knobs": list(self.dead_knobs),
            "support_layers": list(self.support_layers),
            "nc_accuracy": self.nc_accuracy,
            "nc_per_shape": dict(self.nc_per_shape),
            "nc_outcomes":
                [n.to_dict() for n in self.nc_outcomes],
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
    ablations: tuple[GateAblation, ...],
) -> tuple[str, str]:
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
        issues.append(f"nc_accuracy={nc_acc} < {MIN_NC_ACCURACY}")
    if contamination != 0:
        issues.append(
            f"contamination_count={contamination} != 0"
        )

    cliffs = [
        a.gate for a in ablations
        if a.classification == GateClassification.PRIMARY_CLIFF.value
    ]
    dead = [
        a.gate for a in ablations
        if a.classification == GateClassification.DEAD_KNOB.value
    ]
    support = [
        a.gate for a in ablations
        if a.classification == GateClassification.SUPPORT_LAYER.value
    ]

    if issues:
        return "NONE", "; ".join(issues)

    # Recommendation logic per directive.
    if not cliffs and dead:
        return (
            "GATE_DEPRECATION_CANDIDATE",
            f"all gates are DEAD_KNOB: {dead}",
        )
    if len(cliffs) >= 1 and not dead:
        return (
            "GATE_STACK_CONFIRMED",
            f"primary_cliffs={cliffs}; support_layers={support}",
        )
    if cliffs and dead:
        return (
            "GATE_STACK_REORDER",
            (
                f"primary_cliffs={cliffs}; dead_knobs={dead}; "
                "deprecate dead and elevate cliffs"
            ),
        )
    # Mixed support-only — no cliff, no dead.
    return (
        "GATE_STACK_REORDER",
        f"no PRIMARY_CLIFF; all gates SUPPORT_LAYER: {support}",
    )


def build_gate_ablation_report(
    *, started_at: datetime, finished_at: datetime,
) -> GateAblationReport:
    chains = all_chains()
    attack_count = sum(1 for c in chains if c.is_attack)
    transition_count = (
        (len(chains) + len(ALL_NCS)) * transitions_per_chain()
    )

    baseline, baseline_outs = run_baseline(chains)
    ablations: list[GateAblation] = []
    for gate in ablated_gates():
        masked = run_ablation(gate, chains, baseline_outs)
        max_d = _max_delta(baseline, masked)
        cls = _classify(max_d)
        ablations.append(GateAblation(
            gate=gate.value,
            baseline=baseline, masked=masked,
            deltas=_deltas(baseline, masked),
            max_delta=round(max_d, 6),
            classification=cls.value,
        ))

    cliffs = tuple(
        a.gate for a in ablations
        if a.classification == GateClassification.PRIMARY_CLIFF.value
    )
    dead = tuple(
        a.gate for a in ablations
        if a.classification == GateClassification.DEAD_KNOB.value
    )
    support = tuple(
        a.gate for a in ablations
        if a.classification == GateClassification.SUPPORT_LAYER.value
    )

    nc_acc, nc_per_shape, nc_outs = _run_nc()
    contamination = baseline.contamination_count

    rec, reason = _decide(
        chain_count=len(chains) + len(ALL_NCS),
        attack_count=attack_count,
        transition_count=transition_count,
        nc_acc=nc_acc, contamination=contamination,
        ablations=tuple(ablations),
    )

    payload = {
        "chain_count": len(chains) + len(ALL_NCS),
        "attack_count": attack_count,
        "transition_count": transition_count,
        "baseline": baseline.to_dict(),
        "ablations": [a.to_dict() for a in ablations],
        "primary_cliffs": list(cliffs),
        "dead_knobs": list(dead),
        "support_layers": list(support),
        "nc_accuracy": nc_acc,
        "nc_per_shape": nc_per_shape,
        "nc_outcomes": [n.to_dict() for n in nc_outs],
        "contamination_count": contamination,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return GateAblationReport(
        started_at=started_at,
        finished_at=finished_at,
        chain_count=len(chains) + len(ALL_NCS),
        attack_count=attack_count,
        transition_count=transition_count,
        baseline=baseline,
        ablations=tuple(ablations),
        primary_cliffs=cliffs,
        dead_knobs=dead,
        support_layers=support,
        nc_accuracy=nc_acc,
        nc_per_shape=nc_per_shape,
        nc_outcomes=nc_outs,
        contamination_count=contamination,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "DEAD_KNOB_DELTA",
    "GateAblation",
    "GateAblationReport",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "PRIMARY_CLIFF_DELTA",
    "build_gate_ablation_report",
]
