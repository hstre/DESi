"""DESi v3.123 — multi-signal pre-T10 rule."""
from __future__ import annotations

from .report import (
    V3123Report,
    build_pre_t10_multisignal_artifact,
    build_report,
)
from .rule import (
    allowed_pool_count, blocked_pool_count,
    final_far, final_tpr, pools_allowed,
    pools_blocked, rule_allows_t10,
    rule_complexity, selected_axis,
    selected_rule, selected_t1, selected_t2,
)
from .search import (
    SECOND_AXES, SecondAxis, TwoDRule, all_rules,
    axis_value, best_rule,
)


__all__ = [
    "SECOND_AXES",
    "SecondAxis",
    "TwoDRule",
    "V3123Report",
    "all_rules",
    "allowed_pool_count",
    "axis_value",
    "best_rule",
    "blocked_pool_count",
    "build_pre_t10_multisignal_artifact",
    "build_report",
    "final_far",
    "final_tpr",
    "pools_allowed",
    "pools_blocked",
    "rule_allows_t10",
    "rule_complexity",
    "selected_axis",
    "selected_rule",
    "selected_t1",
    "selected_t2",
]
