"""DESi v3.120 - pre-T10 blindness check rule."""
from __future__ import annotations

from .decision import (
    BLINDNESS_CHECK_THRESHOLD,
    allowed_pool_count,
    blocked_pool_count,
    false_activation_rate,
    historical_gate_flip_count,
    rule_roi,
    true_case_recall,
)
from .report import (
    FALSE_ACTIVATION_CEILING,
    TRUE_RECALL_FLOOR,
    V3120Report,
    build_pre_t10_rule_artifact,
    build_report,
)
from .rule import (
    pool_text_variance,
    pools_allowed,
    pools_blocked,
    rule_allows_t10,
)


__all__ = [
    "BLINDNESS_CHECK_THRESHOLD",
    "FALSE_ACTIVATION_CEILING",
    "TRUE_RECALL_FLOOR",
    "V3120Report",
    "allowed_pool_count",
    "blocked_pool_count",
    "build_pre_t10_rule_artifact",
    "build_report",
    "false_activation_rate",
    "historical_gate_flip_count",
    "pool_text_variance",
    "pools_allowed",
    "pools_blocked",
    "rule_allows_t10",
    "rule_roi",
    "true_case_recall",
]
