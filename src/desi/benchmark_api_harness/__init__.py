"""DESi v33.3 - Benchmark Harness & Blind Runner (read-only).

A general harness that loads BenchmarkTasks, runs the matching DESi
adapter, validates the results, supports blind evaluation and emits
traceable scorecards - without importing or touching a protected
core module. Blind scoring uses only objective result properties, so
DESi cannot adapt its output to a known benchmark.
"""
from __future__ import annotations

from .blind_runner import (
    AnonRun, anon_runs, blind_evaluation_integrity, blind_scores,
    sealed_map,
)
from .harness import adapters, load_tasks, run_all, run_task
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_RAN,
    V333Report, build_harness_artifact, build_report,
    core_separation, harness_metrics, replay_stability,
)
from .result_validator import (
    result_validation, validate, validation_failures,
)
from .scorecard import Scorecard, scorecard_traceability, scorecards


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_RAN",
    "AnonRun",
    "Scorecard",
    "V333Report",
    "adapters",
    "anon_runs",
    "blind_evaluation_integrity",
    "blind_scores",
    "build_harness_artifact",
    "build_report",
    "core_separation",
    "harness_metrics",
    "load_tasks",
    "replay_stability",
    "result_validation",
    "run_all",
    "run_task",
    "scorecard_traceability",
    "scorecards",
    "sealed_map",
    "validate",
    "validation_failures",
]
