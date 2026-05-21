"""DESi v30.1 - Rejection Memory & Risk Ecology (read-only).

Remembers evolution risks from the preserved rejection history:
recurring unsafe ideas, risk clusters and escalation patterns are
made visible. DESi marks risks but never auto-blocks a future
idea - no implicit policy learning, no policy adaptation, no
governance change. Rejected ideas are never deleted.
"""
from __future__ import annotations

from .ecology import (
    governance_neutrality, risk_by_agent, risk_by_invariant,
    risks_are_descriptive_only,
)
from .rejection_history import (
    RejectionEntry, nothing_deleted, rejection_history,
    risk_traceability,
)
from .risk_memory import (
    RiskOccurrence, risk_clusters, risk_occurrences, risk_types,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_POLICY_LEAK,
    VERDICT_REMEMBERED, V301Report, build_rejections_artifact,
    build_report, replay_stability,
)
from .unsafe_patterns import (
    auto_blocks_future_ideas, escalation_pattern,
    recurrent_risks, risk_pattern_visibility,
    unsafe_recurrence_visibility,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_POLICY_LEAK",
    "VERDICT_REMEMBERED",
    "RejectionEntry",
    "RiskOccurrence",
    "V301Report",
    "auto_blocks_future_ideas",
    "build_rejections_artifact",
    "build_report",
    "escalation_pattern",
    "governance_neutrality",
    "nothing_deleted",
    "recurrent_risks",
    "rejection_history",
    "risk_by_agent",
    "risk_by_invariant",
    "risk_clusters",
    "risk_occurrences",
    "risk_pattern_visibility",
    "risk_traceability",
    "risk_types",
    "risks_are_descriptive_only",
    "replay_stability",
    "unsafe_recurrence_visibility",
]
