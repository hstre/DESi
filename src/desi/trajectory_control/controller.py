"""v3.26 — passive intervention controller.

The controller never modifies runtime state. For each
trajectory it:

1. Runs the v3.25 observer to obtain predictions.
2. At each state index, consults the policy. If the
   policy returns an action, the controller produces a
   *counterfactual* trajectory by applying the action
   to the existing state sequence.
3. Re-runs labelling and metric computation on the
   counterfactual and reports outcomes side by side.

Closed metric set (directive):

* ``predicted_cliffs``      — sum over trajectories of
  observer-predicted cliff transitions.
* ``true_cliffs``           — sum of ground-truth cliffs
  in the original trajectories.
* ``false_interventions``   — controller acted on a
  trajectory whose original had no true cliff within
  the next two steps from the intervention index.
* ``missed_cliffs``         — controller did not act on
  a true-cliff trajectory.
* ``false_intervention_rate`` —
  ``false_interventions / total_interventions``.
* ``smoothness_improvement`` — mean(pre - post) of
  smoothness across intervened trajectories. Positive
  = passive intervention smoothed the trajectory.

Stop rule (directive): ``false_intervention_rate > 0.2``
triggers ``HALT`` in the recommendation.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.metrics import compute_metrics
from .actions import AppliedAction, apply_action
from .negative_controls import NCKind, all_ncs
from .observer import observe
from .policies import PolicyDecision, decide
from .state import (
    CliffKind, PredictionKind, compute_step_features,
)


@dataclass(frozen=True)
class ControllerOutcome:
    trajectory_id: str
    source: str
    original_cliff_count: int
    counterfactual_cliff_count: int
    decisions: tuple[PolicyDecision, ...]
    applied_actions: tuple[AppliedAction, ...]
    intervened: bool
    pre_smoothness: float
    post_smoothness: float
    false_intervention: bool
    missed_cliff: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "original_cliff_count":
                self.original_cliff_count,
            "counterfactual_cliff_count":
                self.counterfactual_cliff_count,
            "decisions":
                [d.to_dict() for d in self.decisions],
            "applied_actions":
                [a.to_dict() for a in self.applied_actions],
            "intervened": self.intervened,
            "pre_smoothness": self.pre_smoothness,
            "post_smoothness": self.post_smoothness,
            "false_intervention": self.false_intervention,
            "missed_cliff": self.missed_cliff,
        }


def _decisions_for(traj: Trajectory) -> tuple[
    tuple[PolicyDecision, ...],
    tuple[AppliedAction, ...],
    tuple,
]:
    obs = observe(traj)
    features = compute_step_features(traj.states)
    branch_history: list[float] = []
    decisions: list[PolicyDecision] = []
    actions: list[AppliedAction] = []
    current_states = traj.states
    for i, (state, feat, pred) in enumerate(
        zip(traj.states, features, obs.predictions),
    ):
        branch_history.append(state.branch_cost)
        # Only the first warning may trigger an action;
        # later predictions on the counterfactual aren't
        # re-evaluated (passive intervention = one shot).
        if actions:
            decisions.append(PolicyDecision(
                index=i, action=None,
                rationale="already_intervened",
            ))
            continue
        d = decide(state, feat, pred, branch_history)
        decisions.append(d)
        if d.action is not None:
            current_states = apply_action(
                current_states, d.action, i,
            )
            actions.append(AppliedAction(
                action=d.action, intervention_index=i,
            ))
    return (
        tuple(decisions), tuple(actions), current_states,
    )


def _cliff_in_window(
    labels: tuple[str, ...], start: int,
    lookahead: int = 2,
) -> bool:
    for j in range(start + 1, start + 1 + lookahead):
        if 0 <= j < len(labels) and labels[j] != (
            CliffKind.NONE.value
        ):
            return True
    return False


def control_trajectory(traj: Trajectory) -> ControllerOutcome:
    obs = observe(traj)
    original_cliffs = obs.cliff_count
    decisions, actions, counterfactual = _decisions_for(traj)
    counterfactual_obs = observe(Trajectory(
        trajectory_id=traj.trajectory_id,
        source=traj.source, text=traj.text,
        states=counterfactual,
        expected_natural=traj.expected_natural,
    ))
    counterfactual_cliffs = counterfactual_obs.cliff_count

    # Smoothness (from Paper-8 metrics).
    pre_metric = compute_metrics(
        f"{traj.trajectory_id}:orig", traj.states,
    )
    post_metric = compute_metrics(
        f"{traj.trajectory_id}:cf", counterfactual,
    )

    intervened = len(actions) > 0
    if intervened:
        # False intervention: original trajectory had no
        # true cliff within the lookahead window of the
        # first intervention index.
        first_idx = actions[0].intervention_index
        original_labels = obs.cliff_labels
        false_int = not _cliff_in_window(
            original_labels, first_idx, lookahead=2,
        )
        # If the trajectory had ANY true cliff but the
        # controller intervened at a non-cliff window,
        # that's still a false intervention by this strict
        # measure.
        missed = False
    else:
        false_int = False
        missed = original_cliffs > 0

    return ControllerOutcome(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value,
        original_cliff_count=original_cliffs,
        counterfactual_cliff_count=counterfactual_cliffs,
        decisions=decisions, applied_actions=actions,
        intervened=intervened,
        pre_smoothness=pre_metric.smoothness,
        post_smoothness=post_metric.smoothness,
        false_intervention=false_int,
        missed_cliff=missed,
    )


def control_all(
    trajectories: tuple[Trajectory, ...] | None = None,
) -> tuple[ControllerOutcome, ...]:
    trajs = trajectories if trajectories is not None else (
        extract_all_trajectories()
    )
    return tuple(control_trajectory(t) for t in trajs)


__all__ = [
    "ControllerOutcome", "control_all",
    "control_trajectory",
]
