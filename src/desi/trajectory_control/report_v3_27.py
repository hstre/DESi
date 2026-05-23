"""v3.27 — rollback report.

Questions (directive):

* rescued verdicts — count of trajectories where the
  rollback action moved the final state away from
  REJECTED.
* overcontrol cases — count of trajectories where the
  rollback erased a previously-SUPPORTED final state.
* replay stability — fraction of trajectories whose
  TraceLog matches across two independent runs (must
  be 1.0 under a deterministic controller).

Stop rule remains the v3.26 false_intervention_rate
ceiling.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from .negative_controls import NCKind, all_ncs
from .replay_control import (
    control_all_with_rollback, control_with_rollback,
    replay_stability,
)


# Gates
MIN_REPLAY_STABILITY              = 1.0
MAX_NC_ROLLBACK_RATE              = 0.20
MAX_OVERCONTROL_RATE              = 0.10


@dataclass(frozen=True)
class V327Report:
    trajectory_count: int
    nc_count: int
    rollback_count: int
    rescued_verdicts: int
    overcontrol_cases: int
    overcontrol_rate: float
    nc_rollback_count: int
    nc_rollback_rate: float
    per_nc_kind_rollback_rate: dict[str, float]
    replay_stability: float
    answers_rescued_question: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "nc_count": self.nc_count,
            "rollback_count": self.rollback_count,
            "rescued_verdicts": self.rescued_verdicts,
            "overcontrol_cases": self.overcontrol_cases,
            "overcontrol_rate": self.overcontrol_rate,
            "nc_rollback_count": self.nc_rollback_count,
            "nc_rollback_rate": self.nc_rollback_rate,
            "per_nc_kind_rollback_rate":
                dict(self.per_nc_kind_rollback_rate),
            "replay_stability": self.replay_stability,
            "answers_rescued_question":
                self.answers_rescued_question,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V327Report:
    trajs = extract_all_trajectories()
    outcomes = control_all_with_rollback(trajs)
    rollback_count = sum(
        1 for o in outcomes if o.rolled_back
    )
    rescued = sum(1 for o in outcomes if o.rescued)
    overcontrol = sum(
        1 for o in outcomes if o.overcontrol
    )
    over_rate = (
        round(overcontrol / rollback_count, 6)
        if rollback_count else 0.0
    )

    ncs = all_ncs()
    nc_outcomes = [
        control_with_rollback(n.trajectory) for n in ncs
    ]
    nc_rollback = sum(
        1 for o in nc_outcomes if o.rolled_back
    )
    nc_rate = (
        round(nc_rollback / len(ncs), 6) if ncs else 0.0
    )
    per_kind_total: Counter = Counter()
    per_kind_rb: Counter = Counter()
    for nc, o in zip(ncs, nc_outcomes):
        per_kind_total[nc.kind] += 1
        if o.rolled_back:
            per_kind_rb[nc.kind] += 1
    per_kind = {
        k: round(per_kind_rb[k] / per_kind_total[k], 6)
        for k in per_kind_total
    }

    stability = replay_stability(trajs)

    halt = (
        nc_rate > MAX_NC_ROLLBACK_RATE
        or over_rate > MAX_OVERCONTROL_RATE
        or stability < MIN_REPLAY_STABILITY
    )
    if halt:
        verdict = "HALT_ROLLBACK"
    elif rescued > 0:
        verdict = "ROLLBACK_RESCUES_VERDICTS"
    else:
        verdict = "ROLLBACK_NEUTRAL"

    rationale = (
        f"{'PASS' if stability >= MIN_REPLAY_STABILITY else 'FAIL'}: "
        f"replay_stability {stability} >= "
        f"{MIN_REPLAY_STABILITY}",
        f"{'PASS' if nc_rate <= MAX_NC_ROLLBACK_RATE else 'FAIL'}: "
        f"nc_rollback_rate {nc_rate} <= "
        f"{MAX_NC_ROLLBACK_RATE}",
        f"{'PASS' if over_rate <= MAX_OVERCONTROL_RATE else 'FAIL'}: "
        f"overcontrol_rate {over_rate} <= "
        f"{MAX_OVERCONTROL_RATE}",
        f"{'INFO' if rescued > 0 else 'NEUTRAL'}: "
        f"rescued_verdicts {rescued}",
    )

    return V327Report(
        trajectory_count=len(trajs),
        nc_count=len(ncs),
        rollback_count=rollback_count,
        rescued_verdicts=rescued,
        overcontrol_cases=overcontrol,
        overcontrol_rate=over_rate,
        nc_rollback_count=nc_rollback,
        nc_rollback_rate=nc_rate,
        per_nc_kind_rollback_rate=per_kind,
        replay_stability=stability,
        answers_rescued_question=(rescued > 0),
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


__all__ = [
    "MAX_NC_ROLLBACK_RATE", "MAX_OVERCONTROL_RATE",
    "MIN_REPLAY_STABILITY", "V327Report", "build_report",
]
