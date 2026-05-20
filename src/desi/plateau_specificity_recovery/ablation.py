"""v3.39 — per-policy ablation.

Run each selector against the v3.35 cross-class
universe (plateau + causal_leap + support_decay +
frame_collision) so the specificity_score is directly
comparable to v3.35's 0.588 baseline. Overcontrol is
also evaluated on the full corpus and reported as a
separate ``full_corpus_overcontrol`` field for paranoia
(any policy that wakes SUPPORTED trajectories on the
broader corpus should still be visible).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..plateau_cross_transfer.transfer import (
    TargetClass, collect_universe,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .policy import apply_policy
from .selector import SelectorKind, fires


_BRIDGE_REQUIRED = 2.0
_REJECTED        = 3.0
_SUPPORTED       = 4.0


@dataclass(frozen=True)
class PolicyOutcome:
    trajectory_id: str
    selector: str                       # SelectorKind value
    target_class: str                   # TargetClass value
    primary_cause: str
    selector_fired: bool
    original_final_support: float
    counterfactual_final_support: float
    plateau_resolved: bool              # plateau & moved off 2.0
    accidental_rescue: bool             # !plateau & 3.0 -> !3.0
    overcontrol: bool                   # 4.0 -> !4.0

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "selector": self.selector,
            "target_class": self.target_class,
            "primary_cause": self.primary_cause,
            "selector_fired": self.selector_fired,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "plateau_resolved": self.plateau_resolved,
            "accidental_rescue":
                self.accidental_rescue,
            "overcontrol": self.overcontrol,
        }


def _outcome_from(
    traj: Trajectory, selector: str,
    target_class: str, primary_cause: str,
) -> PolicyOutcome:
    fired = fires(selector, traj.states)
    cf = apply_policy(traj.states, selector)
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    is_plateau = target_class == TargetClass.PLATEAU.value
    resolved = (
        is_plateau
        and orig_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
        and fired
    )
    accidental = (
        not is_plateau
        and orig_final == _REJECTED
        and cf_final != _REJECTED
        and fired
    )
    over = (
        orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
        and fired
    )
    return PolicyOutcome(
        trajectory_id=traj.trajectory_id,
        selector=selector, target_class=target_class,
        primary_cause=primary_cause,
        selector_fired=fired,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        plateau_resolved=resolved,
        accidental_rescue=accidental,
        overcontrol=over,
    )


def run_policy(
    selector: str,
) -> tuple[PolicyOutcome, ...]:
    """Run a selector against the v3.35 cross-class
    universe. Same universe as v3.35 so the
    specificity_score is directly comparable to the
    0.588 baseline."""
    trajs = {
        t.trajectory_id: t for t in extract_all_trajectories()
    }
    out: list[PolicyOutcome] = []
    for cco in collect_universe():
        t = trajs[cco.trajectory_id]
        out.append(_outcome_from(
            t, selector, cco.target_class, cco.primary_cause,
        ))
    return tuple(out)


def run_all_policies(
) -> tuple[PolicyOutcome, ...]:
    out: list[PolicyOutcome] = []
    for k in SelectorKind:
        out.extend(run_policy(k.value))
    return tuple(out)


def full_corpus_overcontrol(selector: str) -> int:
    """Count of SUPPORTED trajectories the policy
    rescues on the entire corpus (not just the
    cross-class universe). Used to confirm that the
    selector does not damage healthy trajectories."""
    pids = set(plateau_trajectory_ids())
    n = 0
    for t in extract_all_trajectories():
        if t.trajectory_id in pids:
            continue
        if not fires(selector, t.states):
            continue
        cf = apply_policy(t.states, selector)
        if (
            t.states[-1].support_state == _SUPPORTED
            and cf[-1].support_state != _SUPPORTED
        ):
            n += 1
    return n


__all__ = [
    "PolicyOutcome", "full_corpus_overcontrol",
    "run_all_policies", "run_policy",
]
