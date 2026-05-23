"""DESi v38.1 - Granite Structured Task Validation (read-only eval).

Evaluates REAL captured Granite responses on small structured tasks:
classification, extraction, schema-following, format constraints,
evidence mapping and light audit structuring. Outputs are observed
stochastic evidence graded deterministically; costs are real.
"""
from __future__ import annotations

from .cost_scorecard import (
    avg_cost, cost_efficiency, per_task_cost, total_cost,
)
from .granite_runner import GraniteResult, capture_all, captures, results
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V381Report, build_granite_artifact, build_report,
    granite_metrics, granite_success_rate, hallucination_rate,
    replay_stability, schema_compliance,
)
from .schema_compliance import is_compliant, is_hallucinated
from .structured_tasks import StructuredTask, structured_tasks, task_by_id


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "GraniteResult",
    "StructuredTask",
    "V381Report",
    "avg_cost",
    "build_granite_artifact",
    "build_report",
    "capture_all",
    "captures",
    "cost_efficiency",
    "granite_metrics",
    "granite_success_rate",
    "hallucination_rate",
    "is_compliant",
    "is_hallucinated",
    "per_task_cost",
    "replay_stability",
    "results",
    "schema_compliance",
    "structured_tasks",
    "task_by_id",
    "total_cost",
]
