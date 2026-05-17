"""v3.30 — cause-aware control report.

Pflichtmetriken (directive):

* ``rescued_verdicts`` — count of trajectories whose
  REJECTED final state was lifted by a cause-specific
  action.
* ``overcontrol``      — count of SUPPORTED trajectories
  the controller demoted.
* ``nc_interventions`` — count of NC trajectories the
  controller acted on (must be zero — NCs classify
  UNKNOWN and have no cliff).
* ``smoothness_delta`` — pre-post smoothness summed
  over intervened trajectories. Positive = smoother.
* ``rollback_reduction`` — v3.27 rollback_count minus
  the v3.30 rollback usage count.

Stop rule: ``false_intervention_rate > 0.20`` halts.
Cause-aware controller measures false_intervention as
trajectories where intervention fired but final state
did not change in a beneficial direction.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..epistemic_trajectory.metrics import compute_metrics
from ..trajectory_control.negative_controls import all_ncs
from ..trajectory_control.replay_control import (
    control_all_with_rollback,
)
from .controller import (
    CauseAwareOutcome, control_all, control_trajectory,
)


# Gates
MAX_FALSE_INTERVENTION_RATE     = 0.20
MAX_NC_INTERVENTION_RATE        = 0.20
MIN_REPLAY_STABILITY            = 1.0


_ROUND = 2  # mean_* rounding for cross-process jitter


def _round(x: float, n: int = _ROUND) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V330Report:
    trajectory_count: int
    nc_count: int
    intervened_count: int
    rescued_verdicts: int
    overcontrol_cases: int
    nc_interventions: int
    nc_intervention_rate: float
    false_intervention_rate: float
    rollback_usage_count: int
    rollback_reduction: int
    smoothness_pre_mean: float
    smoothness_post_mean: float
    smoothness_delta: float
    action_distribution: dict[str, int]
    cause_distribution: dict[str, int]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "nc_count": self.nc_count,
            "intervened_count": self.intervened_count,
            "rescued_verdicts": self.rescued_verdicts,
            "overcontrol_cases": self.overcontrol_cases,
            "nc_interventions": self.nc_interventions,
            "nc_intervention_rate":
                self.nc_intervention_rate,
            "false_intervention_rate":
                self.false_intervention_rate,
            "rollback_usage_count":
                self.rollback_usage_count,
            "rollback_reduction":
                self.rollback_reduction,
            "smoothness_pre_mean":
                self.smoothness_pre_mean,
            "smoothness_post_mean":
                self.smoothness_post_mean,
            "smoothness_delta": self.smoothness_delta,
            "action_distribution":
                dict(self.action_distribution),
            "cause_distribution":
                dict(self.cause_distribution),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _v327_rollback_count() -> int:
    return sum(
        1 for o in control_all_with_rollback(
            extract_all_trajectories(),
        )
        if o.rolled_back
    )


def build_report() -> V330Report:
    trajs = extract_all_trajectories()
    outcomes = control_all(trajs)

    intervened = [o for o in outcomes if o.intervened]
    rescued = sum(1 for o in outcomes if o.rescued)
    overcontrol = sum(
        1 for o in outcomes if o.overcontrol
    )
    rollback_usage = sum(
        1 for o in intervened if o.used_rollback
    )

    # NCs
    ncs = all_ncs()
    nc_outcomes = [
        control_trajectory(n.trajectory) for n in ncs
    ]
    nc_intervened = sum(
        1 for o in nc_outcomes if o.intervened
    )
    nc_rate = (
        round(nc_intervened / len(ncs), 6) if ncs else 0.0
    )

    # False intervention: intervened but neither rescued
    # nor produced a beneficial change.
    false_int = sum(
        1 for o in intervened
        if not o.rescued and not (
            o.original_final_support
            < o.counterfactual_final_support
        )
    )
    false_rate = (
        round(false_int / len(intervened), 6)
        if intervened else 0.0
    )

    # Smoothness
    smoothness_pre = []
    smoothness_post = []
    for o in intervened:
        traj = next(
            t for t in trajs
            if t.trajectory_id == o.trajectory_id
        )
        pre = compute_metrics(
            traj.trajectory_id, traj.states,
        ).smoothness
        # Rebuild counterfactual states for post-metric
        from .controller import (
            _CAUSE_TO_ACTION,  # type: ignore[attr-defined]
        )
        from .actions import apply_cause_action
        if o.action is not None:
            cf = apply_cause_action(
                traj.states, o.action, len(traj.states) - 2,
            )
            post = compute_metrics(
                f"{traj.trajectory_id}:cf", cf,
            ).smoothness
        else:
            post = pre
        smoothness_pre.append(pre)
        smoothness_post.append(post)
    pre_mean = (
        _round(sum(smoothness_pre) / len(smoothness_pre))
        if smoothness_pre else 0.0
    )
    post_mean = (
        _round(sum(smoothness_post) / len(smoothness_post))
        if smoothness_post else 0.0
    )
    smoothness_delta = _round(pre_mean - post_mean)

    actions = Counter()
    causes = Counter()
    for o in outcomes:
        causes[o.cause] += 1
        if o.action is not None:
            actions[o.action] += 1

    v327_rb = _v327_rollback_count()
    rollback_reduction = v327_rb - rollback_usage

    halt = false_rate > MAX_FALSE_INTERVENTION_RATE
    if halt:
        verdict = "HALT_FALSE_INTERVENTION"
    elif rollback_reduction > 0 and rescued > 0:
        verdict = (
            "CAUSE_AWARE_CONTROL_REDUCES_ROLLBACKS"
        )
    elif rescued > 0:
        verdict = "CAUSE_AWARE_CONTROL_NEUTRAL_ROLLBACK"
    else:
        verdict = "CAUSE_AWARE_CONTROL_NO_RESCUE"

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"false_intervention_rate {false_rate} <= "
        f"{MAX_FALSE_INTERVENTION_RATE}",
        f"{'PASS' if nc_rate <= MAX_NC_INTERVENTION_RATE else 'FAIL'}: "
        f"nc_intervention_rate {nc_rate} <= "
        f"{MAX_NC_INTERVENTION_RATE}",
        f"{'PASS' if rollback_reduction > 0 else 'NEUTRAL'}: "
        f"rollback_reduction {rollback_reduction} > 0",
        f"INFO: rescued_verdicts {rescued}",
        f"INFO: overcontrol_cases {overcontrol}",
    )

    return V330Report(
        trajectory_count=len(trajs),
        nc_count=len(ncs),
        intervened_count=len(intervened),
        rescued_verdicts=rescued,
        overcontrol_cases=overcontrol,
        nc_interventions=nc_intervened,
        nc_intervention_rate=nc_rate,
        false_intervention_rate=false_rate,
        rollback_usage_count=rollback_usage,
        rollback_reduction=rollback_reduction,
        smoothness_pre_mean=pre_mean,
        smoothness_post_mean=post_mean,
        smoothness_delta=smoothness_delta,
        action_distribution=dict(actions),
        cause_distribution=dict(causes),
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cause_aware_artifact() -> dict[str, object]:
    trajs = extract_all_trajectories()
    outcomes = control_all(trajs)
    return {
        "schema_version": "v3_30_cause_aware_control",
        "outcomes": [
            o.to_dict() for o in outcomes if o.intervened
        ],
    }


__all__ = [
    "MAX_FALSE_INTERVENTION_RATE",
    "MAX_NC_INTERVENTION_RATE",
    "MIN_REPLAY_STABILITY", "V330Report",
    "build_cause_aware_artifact", "build_report",
]
