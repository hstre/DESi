"""v3.48 — per-strategy resolution outcomes.

For each (strategy, trajectory) pair, decide:

* ``resolved``     — original was GAP_DETECTED (1.0)
  and the counterfactual final support is something
  else
* ``overcontrol``  — original was SUPPORTED (4.0)
  and the counterfactual moved off SUPPORTED
* ``nc_resolution_fp`` — counted across the NC set
  (trajectories with original final == 4.0)

Pure-Python; reuses the v3.30 ``control_all`` NC
classification (a "negative control" here is any
trajectory the controller did not need to rescue,
i.e. original SUPPORTED).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..gap_detected.extractor import terminal_gap_cases
from ..gap_detected.state import GAP_DETECTED_STATE
from .strategies import StrategyKind, apply_strategy


_SUPPORTED = 4.0


@dataclass(frozen=True)
class ResolutionOutcome:
    trajectory_id: str
    strategy: str
    original_final_support: float
    counterfactual_final_support: float
    resolved: bool
    overcontrol: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "strategy": self.strategy,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "resolved": self.resolved,
            "overcontrol": self.overcontrol,
        }


def _resolve(
    traj: Trajectory, strategy: str,
) -> ResolutionOutcome:
    cf = apply_strategy(traj.states, strategy)
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    resolved = (
        orig_final == GAP_DETECTED_STATE
        and cf_final != GAP_DETECTED_STATE
    )
    overcontrol = (
        orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
    )
    return ResolutionOutcome(
        trajectory_id=traj.trajectory_id,
        strategy=strategy,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        resolved=resolved, overcontrol=overcontrol,
    )


def resolve_all_strategies_on_gaps(
) -> tuple[ResolutionOutcome, ...]:
    """Apply each strategy to each terminal GAP case.
    Length = 7 strategies × 2 GAPs = 14 outcomes."""
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    trajs = {
        t.trajectory_id: t for t in extract_all_trajectories()
    }
    out: list[ResolutionOutcome] = []
    for c in terminal_gap_cases():
        for k in StrategyKind:
            out.append(_resolve(
                trajs[c.trajectory_id], k.value,
            ))
    return tuple(out)


def resolve_on_corpus(
    strategy: str,
) -> tuple[ResolutionOutcome, ...]:
    """Apply a strategy to every trajectory in the
    corpus. Used to measure overcontrol /
    nc_resolution_fp on healthy SUPPORTED cases."""
    return tuple(
        _resolve(t, strategy)
        for t in extract_all_trajectories()
    )


__all__ = [
    "ResolutionOutcome", "resolve_all_strategies_on_gaps",
    "resolve_on_corpus",
]
