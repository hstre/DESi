"""DESi v34.0 - Drift Benchmark Run (read-only).

Executes six drift-style benchmark tasks through the v33 drift
adapter: belief update, contradiction resolution and evidence
sensitivity produce visible, lineage-tracked claim updates; memory
poisoning and objective drift are resisted; an authority-escalation
attempt is refused. The protected core never drifts.
"""
from __future__ import annotations

from .drift_runner import (
    claim_drift_of, core_drift_total_of, is_refused, result_for,
    run_all, run_one,
)
from .drift_scorecard import DriftScorecard, drift_scorecards
from .drift_tasks import (
    DRIFT_RUN_TASKS, DriftRunTask, drift_run_tasks, task_names,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V340Report, authority_escalation_refused,
    build_drift_run_artifact, build_report,
    claim_lineage_preservation, drift_run_metrics, drift_visibility,
    memory_poisoning_resistance, objective_drift_resistance,
    replay_stability,
)


__all__ = [
    "DRIFT_RUN_TASKS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "DriftRunTask",
    "DriftScorecard",
    "V340Report",
    "authority_escalation_refused",
    "build_drift_run_artifact",
    "build_report",
    "claim_drift_of",
    "claim_lineage_preservation",
    "core_drift_total_of",
    "drift_run_metrics",
    "drift_run_tasks",
    "drift_scorecards",
    "drift_visibility",
    "is_refused",
    "memory_poisoning_resistance",
    "objective_drift_resistance",
    "replay_stability",
    "result_for",
    "run_all",
    "run_one",
    "task_names",
]
