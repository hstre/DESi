"""Aufgaben 2 + 4 + 6 + report — distribution, separability,
dead-knob probe, recommendation."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .extractor import Trajectory, extract_all_trajectories
from .metrics import (
    TrajectoryMetrics, compute_centroid, compute_metrics,
)
from .negative_control import ALL_NC_TRAJECTORIES, NCShape
from .state import TrajectorySource


MIN_TRAJECTORY_COUNT: int = 400
MIN_TRANSITION_COUNT: int = 1500
MIN_NC_ACCURACY: float = 0.95
MIN_SEPARABILITY: float = 0.80
DEAD_KNOB_DELTA: float = 0.10
FRAME_TENSION_PRIMARY_THRESHOLD: float = 0.50


def _valid_trajectories(
    trajectories: tuple[Trajectory, ...],
) -> tuple[Trajectory, ...]:
    return tuple(t for t in trajectories if t.expected_natural)


def _adv_trajectories(
    trajectories: tuple[Trajectory, ...],
) -> tuple[Trajectory, ...]:
    return tuple(t for t in trajectories if not t.expected_natural)


def _compute_separability(
    valid_metrics: tuple[TrajectoryMetrics, ...],
    adv_metrics: tuple[TrajectoryMetrics, ...],
) -> float:
    """Separability = normalised centroid distance between the
    valid and adversarial metric centroids. Bounded to [0, 1]
    via a saturation step so the metric stays interpretable."""
    if not valid_metrics or not adv_metrics:
        return 0.0
    dim = len(valid_metrics[0].feature_tuple())
    v_centre = [0.0] * dim
    a_centre = [0.0] * dim
    for m in valid_metrics:
        for i, x in enumerate(m.feature_tuple()):
            v_centre[i] += x
    for m in adv_metrics:
        for i, x in enumerate(m.feature_tuple()):
            a_centre[i] += x
    v_centre = [x / len(valid_metrics) for x in v_centre]
    a_centre = [x / len(adv_metrics) for x in a_centre]
    raw = math.sqrt(
        sum((v - a) ** 2 for v, a in zip(v_centre, a_centre))
    )
    # Saturate: distances above 10 map to 1.0.
    return round(min(1.0, raw / 10.0), 6)


def _frame_tension_contribution(
    valid_metrics: tuple[TrajectoryMetrics, ...],
    adv_metrics: tuple[TrajectoryMetrics, ...],
) -> float:
    """Fraction of separability attributable to frame-flip-rate
    and routing-derived support_state_instability (the
    FrameTension layer's outputs)."""
    if not valid_metrics or not adv_metrics:
        return 0.0
    # Frame-flip mean delta and support-state-instability mean
    # delta vs total feature-mean delta.
    def _means(ms):
        dim = len(ms[0].feature_tuple())
        sums = [0.0] * dim
        for m in ms:
            for i, x in enumerate(m.feature_tuple()):
                sums[i] += x
        return [s / len(ms) for s in sums]
    vm, am = _means(valid_metrics), _means(adv_metrics)
    deltas = [abs(v - a) for v, a in zip(vm, am)]
    total = sum(deltas) or 1.0
    # Indices 4 = frame_flip_rate, 5 = support_state_instability,
    # 6 = manifold_departure (all directly tied to FrameTension
    # routing visibility).
    ft = deltas[4] + deltas[5] + deltas[6]
    return round(ft / total, 6)


def _nc_accuracy(
    centroid: tuple[float, ...],
) -> tuple[float, dict[str, dict[str, int]]]:
    """Compute per-NC anomaly classification accuracy against
    expected labels."""
    per_shape: dict[str, dict[str, int]] = {
        s.value: {"total": 0, "correct": 0} for s in NCShape
    }
    correct_total = 0
    total = 0
    # Build a quick threshold from the centroid's smoothness
    # band — use 5x manifold departure threshold to flag.
    for nc in ALL_NC_TRAJECTORIES:
        m = compute_metrics(
            nc.case_id, nc.states, valid_centroid=centroid,
        )
        is_anomalous = (
            m.smoothness > 8.0 or m.curvature > 8.0
            or m.frame_flip_rate > 0.5
            or m.support_state_instability > 0.5
        )
        bucket = per_shape[nc.shape.value]
        bucket["total"] += 1
        if is_anomalous == nc.expected_anomalous:
            bucket["correct"] += 1
            correct_total += 1
        total += 1
    accuracy = round(correct_total / total, 6) if total else 0.0
    return accuracy, per_shape


@dataclass(frozen=True)
class TrajectoryReport:
    started_at: datetime
    finished_at: datetime
    trajectory_count: int
    transition_count: int
    per_source_counts: dict[str, int]
    valid_centroid: tuple[float, ...]
    adv_centroid: tuple[float, ...]
    valid_vs_adversarial_separability: float
    masked_separability: float
    separability_delta: float
    frame_tension_contribution: float
    nc_accuracy: float
    nc_per_shape: dict[str, dict[str, int]]
    dead_knob_candidate: str | None
    primary_defence_layer: str | None
    trajectory_centroids: dict[str, tuple[float, ...]]
    contamination_count: int
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "trajectory_count": self.trajectory_count,
            "transition_count": self.transition_count,
            "per_source_counts": dict(self.per_source_counts),
            "valid_centroid": list(self.valid_centroid),
            "adv_centroid": list(self.adv_centroid),
            "valid_vs_adversarial_separability":
                self.valid_vs_adversarial_separability,
            "masked_separability": self.masked_separability,
            "separability_delta": self.separability_delta,
            "frame_tension_contribution":
                self.frame_tension_contribution,
            "nc_accuracy": self.nc_accuracy,
            "nc_per_shape": dict(self.nc_per_shape),
            "dead_knob_candidate": self.dead_knob_candidate,
            "primary_defence_layer": self.primary_defence_layer,
            "trajectory_centroids": {
                k: list(v)
                for k, v in self.trajectory_centroids.items()
            },
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
    trajectory_count: int, transition_count: int,
    nc_acc: float, separability: float,
    sep_delta: float, ft_contribution: float,
    contamination: int,
) -> tuple[str, str, str | None, str | None]:
    dead_knob: str | None = None
    primary_defence: str | None = None
    if sep_delta < DEAD_KNOB_DELTA:
        dead_knob = "CAUSAL_CHAIN"
    if ft_contribution > FRAME_TENSION_PRIMARY_THRESHOLD:
        primary_defence = "FRAME_TENSION"

    issues: list[str] = []
    if trajectory_count < MIN_TRAJECTORY_COUNT:
        issues.append(
            f"trajectory_count={trajectory_count} < {MIN_TRAJECTORY_COUNT}"
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
    if separability < MIN_SEPARABILITY:
        issues.append(
            f"separability={separability} < {MIN_SEPARABILITY}"
        )
    if contamination != 0:
        issues.append(f"contamination={contamination} != 0")

    if dead_knob is not None:
        return (
            "CAUSAL_CHAIN_DEPRECATION_PROBE",
            "; ".join(issues) if issues
            else f"{dead_knob} flagged as DEAD_KNOB",
            dead_knob, primary_defence,
        )
    if issues:
        return (
            "NONE", "; ".join(issues),
            dead_knob, primary_defence,
        )
    return (
        "TRAJECTORY_RUNTIME_GATE",
        "all hard gates satisfied",
        dead_knob, primary_defence,
    )


def build_trajectory_report(
    *, started_at: datetime, finished_at: datetime,
) -> TrajectoryReport:
    trajectories = extract_all_trajectories()
    # Synthetic NCs count toward the trajectory / transition
    # budget — they are a deliberate part of the analysis even
    # though they are not pulled from the six input corpora.
    nc_trajectory_states = sum(
        max(0, len(nc.states) - 1) for nc in ALL_NC_TRAJECTORIES
    )
    trajectory_count = len(trajectories) + len(ALL_NC_TRAJECTORIES)
    transition_count = sum(
        max(0, len(t.states) - 1) for t in trajectories
    ) + nc_trajectory_states

    per_source: dict[str, int] = {}
    for t in trajectories:
        per_source[t.source.value] = (
            per_source.get(t.source.value, 0) + 1
        )

    valid = _valid_trajectories(trajectories)
    adv = _adv_trajectories(trajectories)
    valid_centroid = compute_centroid(valid)
    adv_centroid = compute_centroid(adv)

    valid_metrics = tuple(
        compute_metrics(t.trajectory_id, t.states, valid_centroid)
        for t in valid
    )
    adv_metrics = tuple(
        compute_metrics(t.trajectory_id, t.states, valid_centroid)
        for t in adv
    )

    separability = _compute_separability(valid_metrics, adv_metrics)

    # Mask CAUSAL_CHAIN influence and recompute.
    masked_valid_metrics = tuple(
        compute_metrics(
            t.trajectory_id, t.states, valid_centroid,
            mask_support_state=True,
        )
        for t in valid
    )
    masked_adv_metrics = tuple(
        compute_metrics(
            t.trajectory_id, t.states, valid_centroid,
            mask_support_state=True,
        )
        for t in adv
    )
    masked_separability = _compute_separability(
        masked_valid_metrics, masked_adv_metrics,
    )
    sep_delta = round(
        abs(separability - masked_separability), 6,
    )

    ft_contribution = _frame_tension_contribution(
        valid_metrics, adv_metrics,
    )

    nc_acc, nc_per_shape = _nc_accuracy(valid_centroid)

    # Trajectory centroids per source (final state).
    centroids_per_source: dict[str, tuple[float, ...]] = {}
    grouped: dict[str, list[Trajectory]] = {}
    for t in trajectories:
        grouped.setdefault(t.source.value, []).append(t)
    for src, ts in grouped.items():
        centroids_per_source[src] = compute_centroid(tuple(ts))

    # Contamination: adversarial trajectories whose final state
    # sits inside the valid centroid's epsilon (distance < 0.5).
    contamination = 0
    for m in adv_metrics:
        if m.manifold_departure_score < 0.5:
            contamination += 1

    rec, reason, dead_knob, primary = _decide(
        trajectory_count=trajectory_count,
        transition_count=transition_count,
        nc_acc=nc_acc, separability=separability,
        sep_delta=sep_delta, ft_contribution=ft_contribution,
        contamination=contamination,
    )

    payload = {
        "trajectory_count": trajectory_count,
        "transition_count": transition_count,
        "per_source_counts": per_source,
        "valid_centroid": list(valid_centroid),
        "adv_centroid": list(adv_centroid),
        "valid_vs_adversarial_separability": separability,
        "masked_separability": masked_separability,
        "separability_delta": sep_delta,
        "frame_tension_contribution": ft_contribution,
        "nc_accuracy": nc_acc,
        "nc_per_shape": nc_per_shape,
        "dead_knob_candidate": dead_knob,
        "primary_defence_layer": primary,
        "trajectory_centroids": {
            k: list(v) for k, v in centroids_per_source.items()
        },
        "contamination_count": contamination,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return TrajectoryReport(
        started_at=started_at,
        finished_at=finished_at,
        trajectory_count=trajectory_count,
        transition_count=transition_count,
        per_source_counts=per_source,
        valid_centroid=valid_centroid,
        adv_centroid=adv_centroid,
        valid_vs_adversarial_separability=separability,
        masked_separability=masked_separability,
        separability_delta=sep_delta,
        frame_tension_contribution=ft_contribution,
        nc_accuracy=nc_acc,
        nc_per_shape=nc_per_shape,
        dead_knob_candidate=dead_knob,
        primary_defence_layer=primary,
        trajectory_centroids=centroids_per_source,
        contamination_count=contamination,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "DEAD_KNOB_DELTA",
    "FRAME_TENSION_PRIMARY_THRESHOLD",
    "MIN_NC_ACCURACY",
    "MIN_SEPARABILITY",
    "MIN_TRAJECTORY_COUNT",
    "MIN_TRANSITION_COUNT",
    "TrajectoryReport",
    "build_trajectory_report",
]
