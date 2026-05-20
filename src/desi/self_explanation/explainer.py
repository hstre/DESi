"""v3.37 — DESi self-explanation.

For every trajectory that Strategy B moved (the 20
plateau resolutions and the 14 unexpected
CAUSAL_LEAP rescues), produce a structured
"why did I rescue this trajectory?" record.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..plateau_cross_transfer.transfer import (
    CrossClassOutcome, collect_universe,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from ..trajectory_root_cause.classifier import (
    classify_trajectory,
)
from .attribution import (
    confidence_hold_was_noop, decisive_dimension,
    first_changed_dimension,
)
from .counterfactual import (
    DimensionDelta, per_dimension_deltas,
    strategy_b_counterfactual,
)


# Plateau cause anchor (v3.32 finding: all 20 plateau
# trajectories share CONFIDENCE_OSCILLATION as primary
# cause). This is the reference against which "identical
# to plateau cause?" is evaluated.
PLATEAU_PRIMARY_CAUSE = "CONFIDENCE_OSCILLATION"


@dataclass(frozen=True)
class SelfExplanation:
    trajectory_id: str
    target_class: str               # plateau / causal_leap
    original_primary_cause: str
    identical_to_plateau_cause: bool
    original_final_support: float
    counterfactual_final_support: float
    verdict_changed: bool
    first_changed_dimension: str | None
    decisive_dimension: str | None
    confidence_hold_noop: bool
    deltas: tuple[DimensionDelta, ...]
    explained: bool                 # has a decisive dim
    machine_readable_reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "target_class": self.target_class,
            "original_primary_cause":
                self.original_primary_cause,
            "identical_to_plateau_cause":
                self.identical_to_plateau_cause,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "verdict_changed": self.verdict_changed,
            "first_changed_dimension":
                self.first_changed_dimension,
            "decisive_dimension":
                self.decisive_dimension,
            "confidence_hold_noop":
                self.confidence_hold_noop,
            "deltas": [d.to_dict() for d in self.deltas],
            "explained": self.explained,
            "machine_readable_reason":
                self.machine_readable_reason,
        }


def _audit_index(states_len: int) -> int:
    """The intervention index Strategy B uses: n - 3.
    Below it confidence is held; above it is the audit
    step that gets withdrawn."""
    return states_len - 3


def _reason_token(
    decisive: str | None, noop: bool,
    identical_cause: bool,
) -> str:
    if decisive is None:
        return "NO_VERDICT_CHANGE"
    if decisive == "support_state" and noop:
        if identical_cause:
            return "AUDIT_WITHDRAW_ON_PLATEAU_CAUSE"
        return "AUDIT_WITHDRAW_ON_FOREIGN_CAUSE"
    if decisive == "support_state":
        return "AUDIT_WITHDRAW_WITH_CONFIDENCE_LIFT"
    return f"DECISIVE_{decisive.upper()}"


def explain_one(traj: Trajectory) -> SelfExplanation:
    cf = strategy_b_counterfactual(traj.states)
    deltas = per_dimension_deltas(traj.states, cf)
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    changed = orig_final != cf_final
    first = first_changed_dimension(deltas)
    dec = decisive_dimension(traj.states, cf, deltas)
    noop = confidence_hold_was_noop(
        deltas, _audit_index(len(traj.states)),
    )
    primary = classify_trajectory(traj).primary_cause
    identical = primary == PLATEAU_PRIMARY_CAUSE
    target = (
        "plateau"
        if traj.trajectory_id in set(plateau_trajectory_ids())
        else "causal_leap"
    )
    explained = dec is not None and changed
    reason = _reason_token(dec, noop, identical)
    return SelfExplanation(
        trajectory_id=traj.trajectory_id,
        target_class=target,
        original_primary_cause=primary,
        identical_to_plateau_cause=identical,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        verdict_changed=changed,
        first_changed_dimension=first,
        decisive_dimension=dec,
        confidence_hold_noop=noop,
        deltas=deltas,
        explained=explained,
        machine_readable_reason=reason,
    )


def _trajectories_by_id() -> dict[str, Trajectory]:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def collect_movers(
) -> tuple[CrossClassOutcome, ...]:
    """Trajectories that Strategy B moved: resolved
    plateau OR false_rescue."""
    return tuple(
        o for o in collect_universe()
        if o.resolved_plateau or o.false_rescue
    )


def explain_all_movers() -> tuple[SelfExplanation, ...]:
    movers = collect_movers()
    trajs = _trajectories_by_id()
    return tuple(
        explain_one(trajs[o.trajectory_id])
        for o in movers
    )


def explain_unexpected_rescues(
) -> tuple[SelfExplanation, ...]:
    """Subset that the directive's gate counts:
    self_explained_count = explained ∩ false_rescue."""
    trajs = _trajectories_by_id()
    return tuple(
        explain_one(trajs[o.trajectory_id])
        for o in collect_universe() if o.false_rescue
    )


__all__ = [
    "PLATEAU_PRIMARY_CAUSE", "SelfExplanation",
    "collect_movers", "explain_all_movers",
    "explain_one", "explain_unexpected_rescues",
]
