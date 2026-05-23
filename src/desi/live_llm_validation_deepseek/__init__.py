"""DESi v38.2 - DeepSeek V4 Pro Semantic Validation (read-only eval).

Evaluates REAL captured DeepSeek V4 Pro responses on hard semantic
tasks against a REAL Granite baseline. semantic_quality_lift is
DeepSeek's achieved semantic quality; the Granite delta is reported
transparently. Hallucination signals are always surfaced.
"""
from __future__ import annotations

from .audit_semantic_checks import (
    gap_preserved, rubric_score, ungrounded_token_count,
)
from .deepseek_runner import (
    SemanticResult, capture_all, deepseek_results, granite_results,
)
from .reasoning_scorecard import SemanticScorecard, scorecards
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V382Report, build_deepseek_artifact, build_report,
    deepseek_metrics, evidence_gap_preservation, governance_stability,
    hallucination_visibility, replay_stability, semantic_quality_lift,
)
from .semantic_tasks import SemanticTask, semantic_tasks, task_by_id


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "SemanticResult",
    "SemanticScorecard",
    "SemanticTask",
    "V382Report",
    "build_deepseek_artifact",
    "build_report",
    "capture_all",
    "deepseek_metrics",
    "deepseek_results",
    "evidence_gap_preservation",
    "gap_preserved",
    "governance_stability",
    "granite_results",
    "hallucination_visibility",
    "replay_stability",
    "rubric_score",
    "scorecards",
    "semantic_quality_lift",
    "semantic_tasks",
    "task_by_id",
    "ungrounded_token_count",
]
