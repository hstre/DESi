"""DESi v38.3 - Routing & Governance Benchmark (read-only eval).

Routes low-complexity structured tasks to cheap Granite and escalates
only hard semantic tasks to DeepSeek, computing the real cost
reduction versus an all-DeepSeek baseline while preserving quality and
governance. All costs/qualities come from real captures.
"""
from __future__ import annotations

from .cost_optimizer import (
    all_deepseek_cost, all_granite_cost, routed_cost,
    routing_cost_reduction,
)
from .escalation_logic import (
    deepseek_escalation_rate, escalated, should_escalate,
    unnecessary_escalations,
)
from .governance_router import governance_stability, quality_preservation
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V383Report, build_report, build_routing_artifact, replay_stability,
    routing_metrics,
)
from .routing_engine import (
    COMPLEXITY_HIGH, COMPLEXITY_LOW, ROUTE_DEEPSEEK, ROUTE_GRANITE,
    RoutedTask, routed_tasks,
)


__all__ = [
    "COMPLEXITY_HIGH",
    "COMPLEXITY_LOW",
    "REPORT_VERDICTS",
    "ROUTE_DEEPSEEK",
    "ROUTE_GRANITE",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "RoutedTask",
    "V383Report",
    "all_deepseek_cost",
    "all_granite_cost",
    "build_report",
    "build_routing_artifact",
    "deepseek_escalation_rate",
    "escalated",
    "governance_stability",
    "quality_preservation",
    "replay_stability",
    "routed_cost",
    "routed_tasks",
    "routing_cost_reduction",
    "routing_metrics",
    "should_escalate",
    "unnecessary_escalations",
]
