"""v3.29 — survival metrics.

For each rolled-back trajectory, compare the four run
outcomes. "Survival gain" = trajectories whose Run D
(delayed closure) result is strictly better than Run C
(no controller). Better = avoided the REJECTED verdict.

The killer-question metric: how many trajectories were
"rescued" not by the rollback action itself but by the
mere fact that the audit step was skipped?
"""
from __future__ import annotations

from dataclasses import dataclass

from .runs import RunOutcome


_REJECTED = 3.0
_SUPPORTED = 4.0


@dataclass(frozen=True)
class SurvivalComparison:
    trajectory_id: str
    run_a_final: float
    run_b_final: float
    run_c_final: float
    run_d_final: float
    a_avoided_reject: bool
    b_avoided_reject: bool
    c_was_rejected: bool
    d_avoided_reject: bool
    survived_via_delayed_closure: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "run_a_final": self.run_a_final,
            "run_b_final": self.run_b_final,
            "run_c_final": self.run_c_final,
            "run_d_final": self.run_d_final,
            "a_avoided_reject": self.a_avoided_reject,
            "b_avoided_reject": self.b_avoided_reject,
            "c_was_rejected": self.c_was_rejected,
            "d_avoided_reject": self.d_avoided_reject,
            "survived_via_delayed_closure":
                self.survived_via_delayed_closure,
        }


def compare_runs(
    outcomes: tuple[RunOutcome, ...],
) -> SurvivalComparison:
    by_run = {o.run: o for o in outcomes}
    a = by_run["RUN_A_NORMAL"].final_support_state
    b = by_run["RUN_B_NO_ROLLBACK"].final_support_state
    c = by_run["RUN_C_NO_PRUNING"].final_support_state
    d = by_run["RUN_D_DELAYED_CLOSURE"].final_support_state
    a_avoided = a != _REJECTED
    b_avoided = b != _REJECTED
    c_was_reject = c == _REJECTED
    d_avoided = d != _REJECTED
    survived = c_was_reject and d_avoided
    return SurvivalComparison(
        trajectory_id=outcomes[0].trajectory_id,
        run_a_final=a, run_b_final=b,
        run_c_final=c, run_d_final=d,
        a_avoided_reject=a_avoided,
        b_avoided_reject=b_avoided,
        c_was_rejected=c_was_reject,
        d_avoided_reject=d_avoided,
        survived_via_delayed_closure=survived,
    )


__all__ = ["SurvivalComparison", "compare_runs"]
