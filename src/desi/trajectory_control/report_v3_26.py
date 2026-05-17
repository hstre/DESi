"""v3.26 — passive intervention report.

Question: *Verbessert passive Intervention die
trajectory smoothness?*

Stop rule (directive): if
``false_intervention_rate > 0.2`` → ``HALT``.

The recommendation gate emits one of:

* ``PASSIVE_INTERVENTION_IMPROVES_SMOOTHNESS`` — gate
  passes, smoothness improvement positive.
* ``PASSIVE_INTERVENTION_NEUTRAL`` — gate passes,
  smoothness change non-positive.
* ``HALT_FALSE_INTERVENTION`` — stop rule fired.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from .controller import (
    ControllerOutcome, control_all, control_trajectory,
)
from .negative_controls import NCKind, all_ncs
from .observer import observe
from .state import CliffKind


# Gate
MAX_FALSE_INTERVENTION_RATE      = 0.20
MAX_NC_INTERVENTION_RATE         = 0.20


# Smoothness is summed over O(n_states * n_dimensions) so
# its mean carries a larger jitter window than v3.25's
# fractional metrics. 1 decimal is sufficient — the
# improvement gate works on sign of `pre - post`, not on
# absolute value.
_ROUND = 1


def _round(x: float, n: int = _ROUND) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V326Report:
    trajectory_count: int
    nc_count: int
    predicted_cliffs: int
    true_cliffs: int
    interventions: int
    false_interventions: int
    missed_cliffs: int
    false_intervention_rate: float
    nc_intervention_rate: float
    per_nc_kind_intervention_rate: dict[str, float]
    mean_pre_smoothness: float
    mean_post_smoothness: float
    smoothness_improvement: float
    answers_improvement_question: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "nc_count": self.nc_count,
            "predicted_cliffs": self.predicted_cliffs,
            "true_cliffs": self.true_cliffs,
            "interventions": self.interventions,
            "false_interventions":
                self.false_interventions,
            "missed_cliffs": self.missed_cliffs,
            "false_intervention_rate":
                self.false_intervention_rate,
            "nc_intervention_rate":
                self.nc_intervention_rate,
            "per_nc_kind_intervention_rate":
                dict(self.per_nc_kind_intervention_rate),
            "mean_pre_smoothness":
                self.mean_pre_smoothness,
            "mean_post_smoothness":
                self.mean_post_smoothness,
            "smoothness_improvement":
                self.smoothness_improvement,
            "answers_improvement_question":
                self.answers_improvement_question,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V326Report:
    trajs = extract_all_trajectories()
    outcomes = control_all(trajs)
    ncs = all_ncs()

    # Predicted vs true cliffs.
    obs_results = [observe(t) for t in trajs]
    predicted = sum(
        sum(
            1 for p in o.predictions
            if p.prediction in (
                "cliff_next_step", "cliff_two_step",
            )
        )
        for o in obs_results
    )
    true_cliffs = sum(o.cliff_count for o in obs_results)

    interventions = sum(1 for o in outcomes if o.intervened)
    false_int = sum(
        1 for o in outcomes if o.false_intervention
    )
    missed = sum(1 for o in outcomes if o.missed_cliff)
    false_rate = (
        round(false_int / interventions, 6)
        if interventions else 0.0
    )

    # NC controller behaviour.
    nc_outcomes = tuple(
        control_trajectory(n.trajectory) for n in ncs
    )
    nc_intervened = sum(
        1 for o in nc_outcomes if o.intervened
    )
    nc_rate = (
        round(nc_intervened / len(ncs), 6) if ncs else 0.0
    )
    per_kind_total: Counter = Counter()
    per_kind_int: Counter = Counter()
    for nc, o in zip(ncs, nc_outcomes):
        per_kind_total[nc.kind] += 1
        if o.intervened:
            per_kind_int[nc.kind] += 1
    per_kind = {
        k: round(per_kind_int[k] / per_kind_total[k], 6)
        for k in per_kind_total
    }

    # Smoothness over intervened trajectories.
    intervened_outcomes = [
        o for o in outcomes if o.intervened
    ]
    if intervened_outcomes:
        mean_pre = _round(
            sum(o.pre_smoothness for o in intervened_outcomes)
            / len(intervened_outcomes),
        )
        mean_post = _round(
            sum(o.post_smoothness for o in intervened_outcomes)
            / len(intervened_outcomes),
        )
        improvement = _round(mean_pre - mean_post)
    else:
        mean_pre = 0.0
        mean_post = 0.0
        improvement = 0.0

    # Decide recommendation
    halt = false_rate > MAX_FALSE_INTERVENTION_RATE
    if halt:
        verdict = "HALT_FALSE_INTERVENTION"
    elif improvement > 0:
        verdict = "PASSIVE_INTERVENTION_IMPROVES_SMOOTHNESS"
    else:
        verdict = "PASSIVE_INTERVENTION_NEUTRAL"

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"false_intervention_rate {false_rate} <= "
        f"{MAX_FALSE_INTERVENTION_RATE}",
        f"{'PASS' if nc_rate <= MAX_NC_INTERVENTION_RATE else 'FAIL'}: "
        f"nc_intervention_rate {nc_rate} <= "
        f"{MAX_NC_INTERVENTION_RATE}",
        f"{'PASS' if improvement > 0 else 'NEUTRAL'}: "
        f"smoothness_improvement {improvement}",
    )

    return V326Report(
        trajectory_count=len(trajs),
        nc_count=len(ncs),
        predicted_cliffs=predicted,
        true_cliffs=true_cliffs,
        interventions=interventions,
        false_interventions=false_int,
        missed_cliffs=missed,
        false_intervention_rate=false_rate,
        nc_intervention_rate=nc_rate,
        per_nc_kind_intervention_rate=per_kind,
        mean_pre_smoothness=mean_pre,
        mean_post_smoothness=mean_post,
        smoothness_improvement=improvement,
        answers_improvement_question=(improvement > 0),
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


__all__ = [
    "MAX_FALSE_INTERVENTION_RATE",
    "MAX_NC_INTERVENTION_RATE", "V326Report",
    "build_report",
]
