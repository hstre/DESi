"""DESi v3.29 — counterfactual survival probe.

For each trajectory rolled back by the v3.27 controller,
run four controller configurations and compare final-
state outcomes. Killer-question metric: how many of
v3.27's rescues came from rollback specifically vs from
simply not committing to an audit verdict (delayed
closure).
"""
from __future__ import annotations

from .report import (
    V329Report, build_report, build_survival_artifact,
)
from .runs import (
    RunKind, RunOutcome, all_runs,
    rollback_trajectory_ids, run_a_normal,
    run_b_no_rollback, run_c_no_pruning,
    run_d_delayed_closure,
)
from .survival import SurvivalComparison, compare_runs


__all__ = [
    "RunKind", "RunOutcome", "SurvivalComparison",
    "V329Report", "all_runs",
    "build_report", "build_survival_artifact",
    "compare_runs", "rollback_trajectory_ids",
    "run_a_normal", "run_b_no_rollback",
    "run_c_no_pruning", "run_d_delayed_closure",
]
