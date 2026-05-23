"""DESi v2.5 inference-rule coverage audit — read-only."""
from __future__ import annotations

from .categories import AttemptedRule, MissingRuleClass
from .metrics import (
    RuleCoverageMetrics,
    compute_rule_coverage_metrics,
    dominant_missing_rule_class,
)
from .report import (
    RuleCoverageReport,
    build_rule_coverage_report,
    compute_report_replay_hash,
)
from .runner import RuleCoverageRun, RuleCoverageRunner
from .trace import (
    RuleCoverageTrace,
    classify_missing_rule,
    trace_replay_hash,
)

__all__ = [
    "AttemptedRule",
    "MissingRuleClass",
    "RuleCoverageMetrics",
    "RuleCoverageReport",
    "RuleCoverageRun",
    "RuleCoverageRunner",
    "RuleCoverageTrace",
    "build_rule_coverage_report",
    "classify_missing_rule",
    "compute_report_replay_hash",
    "compute_rule_coverage_metrics",
    "dominant_missing_rule_class",
    "trace_replay_hash",
]
