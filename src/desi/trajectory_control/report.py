"""v3.25 — observer report.

Question: *Kann DESi einen Cliff ≥2 Schritte vorher
erkennen?*

Measured by:

* ``two_step_warning_rate`` — fraction of trajectories
  carrying ≥1 true cliff for which the observer raised
  ``CLIFF_TWO_STEP`` (or ``CLIFF_NEXT_STEP``) at an
  index ≤ cliff_index − 1.
* ``cliff_precision`` / ``cliff_recall`` — over all
  (trajectory, state_index) pairs, treating
  ``predicted_proximity ≤ 2`` as the positive class and
  ``label != NONE`` as the true class.

The report also records false-positive activations on
the four NC kinds — *Greift DESi unnötig ein?* — even
though v3.25 issues no interventions. NC false-positive
rate is the fraction of NCs on which the observer
raised any cliff prediction.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from .negative_controls import all_ncs
from .observer import (
    TrajectoryObservation, observe,
)
from .risk import TrajectoryRisk, compute_risk
from .state import compute_step_features, CliffKind, PredictionKind


# Gate thresholds for the v3.25 question.
MIN_TWO_STEP_WARNING_RATE     = 0.80
MAX_NC_FALSE_POSITIVE_RATE    = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


# Aggregate means (mean_*) are rounded coarsely so tiny
# float-boundary jitter — driven by Python's hash
# randomization affecting dict iteration order in
# upstream frame-detector code — does not flip the
# artifact pin. Cosine signs at exactly zero can drift
# by ~1 reversal across runs, shifting
# ``sum(reversals)/total_transitions`` by ~1/1586 ≈ 6e-4.
_MEAN_ROUND = 2


@dataclass(frozen=True)
class V325Report:
    trajectory_count: int
    nc_count: int
    cliff_count: int
    trajectories_with_cliffs: int
    two_step_warning_rate: float
    cliff_precision: float
    cliff_recall: float
    nc_false_positive_rate: float
    per_nc_kind_false_positive: dict[str, float]
    mean_cliff_proximity: float
    mean_confidence_variance: float
    mean_branch_acceleration: float
    mean_oscillation_risk: float
    mean_support_decay: float
    answers_two_step_question: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "nc_count": self.nc_count,
            "cliff_count": self.cliff_count,
            "trajectories_with_cliffs":
                self.trajectories_with_cliffs,
            "two_step_warning_rate":
                self.two_step_warning_rate,
            "cliff_precision": self.cliff_precision,
            "cliff_recall": self.cliff_recall,
            "nc_false_positive_rate":
                self.nc_false_positive_rate,
            "per_nc_kind_false_positive":
                dict(self.per_nc_kind_false_positive),
            "mean_cliff_proximity":
                self.mean_cliff_proximity,
            "mean_confidence_variance":
                self.mean_confidence_variance,
            "mean_branch_acceleration":
                self.mean_branch_acceleration,
            "mean_oscillation_risk":
                self.mean_oscillation_risk,
            "mean_support_decay":
                self.mean_support_decay,
            "answers_two_step_question":
                self.answers_two_step_question,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _evaluate_pair_metrics(
    observations: tuple[TrajectoryObservation, ...],
) -> tuple[float, float]:
    """Precision / recall over all (traj, idx) pairs."""
    tp = fp = fn = 0
    for obs in observations:
        labels = obs.cliff_labels
        preds = obs.predictions
        for i, (label, pred) in enumerate(zip(labels, preds)):
            # Look-ahead window for "did a cliff land near here":
            # [i+1, i+2]
            ahead_cliff = any(
                j < len(labels)
                and labels[j] != CliffKind.NONE.value
                for j in (i + 1, i + 2)
            )
            predicted = (
                pred.prediction in (
                    PredictionKind.CLIFF_NEXT_STEP.value,
                    PredictionKind.CLIFF_TWO_STEP.value,
                )
            )
            if predicted and ahead_cliff:
                tp += 1
            elif predicted and not ahead_cliff:
                fp += 1
            elif not predicted and ahead_cliff:
                fn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return _round(prec), _round(rec)


def _nc_false_positive_rate(
    ncs: tuple, observations: tuple[TrajectoryObservation, ...],
) -> tuple[float, dict[str, float]]:
    by_kind_total: Counter = Counter()
    by_kind_fp: Counter = Counter()
    total_fp = 0
    for nc, obs in zip(ncs, observations):
        by_kind_total[nc.kind] += 1
        fired = any(
            p.prediction in (
                PredictionKind.CLIFF_NEXT_STEP.value,
                PredictionKind.CLIFF_TWO_STEP.value,
            )
            for p in obs.predictions
        )
        if fired:
            by_kind_fp[nc.kind] += 1
            total_fp += 1
    overall = (
        _round(total_fp / len(ncs)) if ncs else 0.0
    )
    per_kind = {
        k: _round(by_kind_fp[k] / by_kind_total[k])
        for k in by_kind_total
    }
    return overall, per_kind


def build_report() -> V325Report:
    trajectories = extract_all_trajectories()
    ncs = all_ncs()

    trajectory_observations = tuple(
        observe(t) for t in trajectories
    )
    nc_observations = tuple(
        observe(n.trajectory) for n in ncs
    )

    cliff_count = sum(
        o.cliff_count for o in trajectory_observations
    )
    traj_with_cliffs = [
        o for o in trajectory_observations
        if o.cliff_count > 0
    ]
    two_step_warning_rate = _round(
        sum(
            1 for o in traj_with_cliffs
            if o.has_two_step_warning
        ) / len(traj_with_cliffs)
        if traj_with_cliffs else 0.0,
    )

    precision, recall = _evaluate_pair_metrics(
        trajectory_observations,
    )
    nc_fp_rate, per_kind_fp = _nc_false_positive_rate(
        ncs, nc_observations,
    )

    risks = [
        compute_risk(
            t.states, observation=obs,
            trajectory_id=t.trajectory_id,
        )
        for t, obs in zip(trajectories, trajectory_observations)
    ]
    n = len(risks)
    mean_prox = _round(
        sum(r.cliff_proximity for r in risks) / n
        if n else 0.0, _MEAN_ROUND,
    )
    mean_conf_var = _round(
        sum(r.confidence_variance for r in risks) / n
        if n else 0.0, _MEAN_ROUND,
    )
    mean_branch_acc = _round(
        sum(r.branch_acceleration for r in risks) / n
        if n else 0.0, _MEAN_ROUND,
    )
    mean_osc = _round(
        sum(r.oscillation_risk for r in risks) / n
        if n else 0.0, _MEAN_ROUND,
    )
    mean_decay = _round(
        sum(r.support_decay for r in risks) / n
        if n else 0.0, _MEAN_ROUND,
    )

    answers = (
        two_step_warning_rate >= MIN_TWO_STEP_WARNING_RATE
        and nc_fp_rate <= MAX_NC_FALSE_POSITIVE_RATE
    )

    return V325Report(
        trajectory_count=len(trajectories),
        nc_count=len(ncs),
        cliff_count=cliff_count,
        trajectories_with_cliffs=len(traj_with_cliffs),
        two_step_warning_rate=two_step_warning_rate,
        cliff_precision=precision,
        cliff_recall=recall,
        nc_false_positive_rate=nc_fp_rate,
        per_nc_kind_false_positive=per_kind_fp,
        mean_cliff_proximity=mean_prox,
        mean_confidence_variance=mean_conf_var,
        mean_branch_acceleration=mean_branch_acc,
        mean_oscillation_risk=mean_osc,
        mean_support_decay=mean_decay,
        answers_two_step_question=answers,
    )


__all__ = [
    "MAX_NC_FALSE_POSITIVE_RATE",
    "MIN_TWO_STEP_WARNING_RATE", "V325Report",
    "build_report",
]
