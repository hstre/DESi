"""v3.27 — controller with rollback + replay verification.

Extends the v3.26 controller with the
``rollback_last_transition`` action and produces a
``TraceLog`` per trajectory. The v3.27 metrics are:

* ``rescued_verdicts``  — count of trajectories whose
  original final state was REJECTED but the
  counterfactual's final state is not.
* ``overcontrol_cases`` — count of trajectories whose
  original final state was SUPPORTED but the
  counterfactual's final state is not.
* ``replay_stability`` — fraction of trajectories whose
  TraceLog signature matches itself across two
  independent runs (must equal 1.0 on a deterministic
  controller).

Policy extension: the rollback action is selected when
the observer raises ``CLIFF_NEXT_STEP`` AND the warning
fires at index ``i = n - 2`` (the final transition) —
this is the only point where rolling back can actually
"rescue" a verdict.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..epistemic_trajectory.state import DIMENSION_NAMES
from .actions import (
    ActionKind, AppliedAction, apply_action,
)
from .observer import observe
from .policies import decide
from .rollback import (
    RollbackKind, apply_rollback_last_transition,
)
from .state import (
    CliffKind, PredictionKind, compute_step_features,
)
from .trace import TraceEntry, TraceLog


_IDX_SUPPORT = DIMENSION_NAMES.index("support_state")
_SUPPORTED_STATE = 4.0


@dataclass(frozen=True)
class RollbackOutcome:
    trajectory_id: str
    source: str
    original_final_support: float
    counterfactual_final_support: float
    rolled_back: bool
    rescued: bool
    overcontrol: bool
    trace: TraceLog

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "rolled_back": self.rolled_back,
            "rescued": self.rescued,
            "overcontrol": self.overcontrol,
            "trace": self.trace.to_dict(),
        }


# Rollback at the final transition is the only point
# where the action can change the trajectory's final
# verdict. The risk-score floor here is intentionally
# high (≥ 0.6) to keep overcontrol on healthy trajectories
# under the 0.10 ceiling — we only roll back when the
# observer is reasonably confident the audit step is
# about to commit to a non-supported verdict.
_FINAL_ROLLBACK_RISK_FLOOR = 0.6


def _policy_with_rollback(
    state, feat, prediction, branch_history,
    *, is_final_warning: bool,
):
    """Wrapper around the v3.26 policy: elevates
    ``rollback_last_transition`` when the predictor
    raises a high-confidence warning at the
    final-transition index."""
    base = decide(state, feat, prediction, branch_history)
    if is_final_warning and (
        prediction.risk_score >= _FINAL_ROLLBACK_RISK_FLOOR
    ):
        return type(base)(
            index=base.index,
            action=RollbackKind.ROLLBACK_LAST_TRANSITION.value,
            rationale="final_warning_rollback",
        )
    return base


def _apply_action_with_rollback(
    states, action: str, at: int,
):
    if action == RollbackKind.ROLLBACK_LAST_TRANSITION.value:
        return apply_rollback_last_transition(states, at)
    return apply_action(states, action, at)


def control_with_rollback(traj: Trajectory) -> RollbackOutcome:
    obs = observe(traj)
    features = compute_step_features(traj.states)
    n = len(traj.states)
    # Two-pass selection: collect every candidate action,
    # then pick one. Rollback at the final-transition
    # warning wins; otherwise the earliest warning's
    # action wins (v3.26 semantics).
    branch_history_full: list[float] = [
        s.branch_cost for s in traj.states
    ]
    candidates: list[tuple[int, str, str]] = []
    for i, (state, feat, pred) in enumerate(
        zip(traj.states, features, obs.predictions),
    ):
        is_final = (i == n - 2)
        d = _policy_with_rollback(
            state, feat, pred,
            branch_history_full[: i + 1],
            is_final_warning=is_final,
        )
        if d.action is not None:
            candidates.append((i, d.action, d.rationale))
    chosen: tuple[int, str, str] | None = None
    rollback_candidates = [
        c for c in candidates
        if c[1] == RollbackKind.ROLLBACK_LAST_TRANSITION.value
    ]
    if rollback_candidates:
        chosen = rollback_candidates[-1]
    elif candidates:
        chosen = candidates[0]

    entries: list[TraceEntry] = []
    current = traj.states
    for i in range(n):
        if chosen is not None and i == chosen[0]:
            entries.append(TraceEntry(
                trajectory_id=traj.trajectory_id,
                state_index=i, action=chosen[1],
                rationale=chosen[2],
            ))
            current = _apply_action_with_rollback(
                current, chosen[1], i,
            )
        else:
            entries.append(TraceEntry(
                trajectory_id=traj.trajectory_id,
                state_index=i, action="no_action",
                rationale="not_chosen",
            ))
    acted = chosen is not None
    trace = TraceLog(
        trajectory_id=traj.trajectory_id,
        entries=tuple(entries),
    )
    original_final = traj.states[-1].support_state
    counterfactual_final = current[-1].support_state
    rolled_back = any(
        e.action == RollbackKind.ROLLBACK_LAST_TRANSITION.value
        for e in entries
    )
    # In DESi audit semantics:
    #   4 = LOGICALLY_SUPPORTED, 3 = LOGICALLY_REJECTED,
    #   2 = BRIDGE_REQUIRED, 1 = GAP_DETECTED,
    #   0 = UNDER_LOGICAL_AUDIT (the pre-audit placeholder
    #       that rollback restores).
    # Rolling back from REJECTED (3) to UNDER_AUDIT (0)
    # is a rescue: we have withdrawn the decisive
    # rejection in favour of "needs more work". Rolling
    # back away from SUPPORTED (4) is overcontrol: we
    # threw away a verdict that was already correct.
    rescued = (
        original_final == 3.0
        and counterfactual_final != 3.0
        and acted
    )
    overcontrol = (
        original_final == 4.0
        and counterfactual_final != 4.0
        and acted
    )
    return RollbackOutcome(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value,
        original_final_support=original_final,
        counterfactual_final_support=counterfactual_final,
        rolled_back=rolled_back,
        rescued=rescued,
        overcontrol=overcontrol,
        trace=trace,
    )


def control_all_with_rollback(
    trajectories: tuple[Trajectory, ...] | None = None,
) -> tuple[RollbackOutcome, ...]:
    trajs = trajectories if trajectories is not None else (
        extract_all_trajectories()
    )
    return tuple(control_with_rollback(t) for t in trajs)


def replay_stability(
    trajectories: tuple[Trajectory, ...] | None = None,
) -> float:
    """Run the controller twice and verify each
    trajectory's TraceLog signature is identical."""
    trajs = trajectories if trajectories is not None else (
        extract_all_trajectories()
    )
    first = {
        o.trajectory_id: o.trace.signature()
        for o in control_all_with_rollback(trajs)
    }
    second = {
        o.trajectory_id: o.trace.signature()
        for o in control_all_with_rollback(trajs)
    }
    matches = sum(
        1 for k in first
        if first[k] == second.get(k)
    )
    return round(matches / len(first), 6) if first else 0.0


__all__ = [
    "RollbackOutcome", "control_all_with_rollback",
    "control_with_rollback", "replay_stability",
]
