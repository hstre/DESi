"""v3.29 — counterfactual survival report.

Pflichtmetriken: final verdict, smoothness, branch_cost,
contradiction count, support depth, replay hash — one
column per run kind.

Killerfrage: ``survival_gain`` — count of rolled-back
trajectories whose Run D (delayed closure) avoided the
REJECTED verdict that Run C (no controller) committed
to.

Stop rule: ``survival_gain == 0`` halts Paper 9.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from .runs import (
    RunKind, RunOutcome, all_runs,
    rollback_trajectory_ids,
)
from .survival import SurvivalComparison, compare_runs


@dataclass(frozen=True)
class V329Report:
    rolled_back_count: int
    survival_gain: int
    rollback_only_gain: int      # Run A avoided but Run D didn't
    no_gain_count: int           # neither A nor D rescued
    run_a_avoided_count: int
    run_b_avoided_count: int
    run_c_avoided_count: int
    run_d_avoided_count: int
    paper9_stop: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "rolled_back_count": self.rolled_back_count,
            "survival_gain": self.survival_gain,
            "rollback_only_gain":
                self.rollback_only_gain,
            "no_gain_count": self.no_gain_count,
            "run_a_avoided_count":
                self.run_a_avoided_count,
            "run_b_avoided_count":
                self.run_b_avoided_count,
            "run_c_avoided_count":
                self.run_c_avoided_count,
            "run_d_avoided_count":
                self.run_d_avoided_count,
            "paper9_stop": self.paper9_stop,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _comparisons() -> tuple[SurvivalComparison, ...]:
    ids = set(rollback_trajectory_ids())
    trajs = [
        t for t in extract_all_trajectories()
        if t.trajectory_id in ids
    ]
    out: list[SurvivalComparison] = []
    for t in trajs:
        runs = all_runs(t)
        out.append(compare_runs(runs))
    return tuple(out)


def build_report() -> V329Report:
    comps = _comparisons()
    n = len(comps)
    survival_gain = sum(
        1 for c in comps if c.survived_via_delayed_closure
    )
    a_avoided = sum(1 for c in comps if c.a_avoided_reject)
    b_avoided = sum(1 for c in comps if c.b_avoided_reject)
    c_avoided = sum(
        1 for c in comps if not c.c_was_rejected
    )
    d_avoided = sum(1 for c in comps if c.d_avoided_reject)
    rollback_only = sum(
        1 for c in comps
        if c.a_avoided_reject and not c.d_avoided_reject
    )
    no_gain = sum(
        1 for c in comps
        if not c.a_avoided_reject and not c.d_avoided_reject
    )

    paper9_stop = survival_gain == 0
    if paper9_stop:
        verdict = "PAPER9_STOP_NO_SURVIVAL_GAIN"
    elif survival_gain >= 1 and rollback_only > 0:
        verdict = "BOTH_ROLLBACK_AND_DELAYED_CLOSURE_HELP"
    elif survival_gain >= 1:
        verdict = "DELAYED_CLOSURE_EXPLAINS_RESCUE"
    else:
        verdict = "ROLLBACK_PROVIDES_NO_SURVIVAL_GAIN"

    rationale = (
        f"{'PASS' if survival_gain > 0 else 'FAIL'}: "
        f"survival_gain {survival_gain} > 0",
        f"INFO: run_a_avoided_count {a_avoided}",
        f"INFO: run_b_avoided_count {b_avoided}",
        f"INFO: run_c_avoided_count {c_avoided}",
        f"INFO: run_d_avoided_count {d_avoided}",
        f"INFO: rollback_only_gain {rollback_only}",
        f"INFO: no_gain_count {no_gain}",
    )

    return V329Report(
        rolled_back_count=n,
        survival_gain=survival_gain,
        rollback_only_gain=rollback_only,
        no_gain_count=no_gain,
        run_a_avoided_count=a_avoided,
        run_b_avoided_count=b_avoided,
        run_c_avoided_count=c_avoided,
        run_d_avoided_count=d_avoided,
        paper9_stop=paper9_stop,
        recommendation=verdict, rationale=rationale,
    )


def build_survival_artifact() -> dict[str, object]:
    comps = _comparisons()
    return {
        "schema_version": "v3_29_counterfactual_survival",
        "comparisons": [c.to_dict() for c in comps],
    }


__all__ = ["V329Report", "build_report", "build_survival_artifact"]
