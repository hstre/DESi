"""DESi v36.2 - Logic & Fallacy Benchmarks: LogiQA / ReClor.

Runs locally-vendored LogiQA and ReClor reference datasets through
DESi's deterministic logical-form analyzer: valid forms are judged
valid, fallacies are named, unstated assumptions are surfaced and
distractor options are resisted. Unknown forms are never asserted
valid.
"""
from __future__ import annotations

from .fallacy_detector import (
    FALLACY_FORMS, VALID_FORMS, detect_fallacy, has_fallacy,
    is_valid,
)
from .logic_scorecard import (
    LogicScorecard, all_logic_tasks, logic_scorecards,
    selected_option,
)
from .logiqa_loader import LogicTask, logiqa_tasks
from .reclor_loader import reclor_tasks
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V362Report, assumption_visibility, build_logic_artifact,
    build_report, distractor_resistance, fallacy_detection,
    logic_metrics, logical_consistency, replay_stability,
)


__all__ = [
    "FALLACY_FORMS",
    "REPORT_VERDICTS",
    "VALID_FORMS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "LogicScorecard",
    "LogicTask",
    "V362Report",
    "all_logic_tasks",
    "assumption_visibility",
    "build_logic_artifact",
    "build_report",
    "detect_fallacy",
    "distractor_resistance",
    "fallacy_detection",
    "has_fallacy",
    "is_valid",
    "logic_metrics",
    "logic_scorecards",
    "logical_consistency",
    "logiqa_tasks",
    "reclor_tasks",
    "replay_stability",
    "selected_option",
]
