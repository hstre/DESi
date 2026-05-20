"""DESi v23.4 - Targeted ICRL Follow-Up: Final Follow-Up
Verdict (read-only).

Aggregates one signal per dimension from the v23.0-v23.3
layers, checks the six-condition Concept Gate, classifies the
follow-up on a closed A-E taxonomy, and assembles the revised
v2 paper plus the German go/no-go document. DESi is presented
as a complementary, read-only governance layer scoped to the
synthetic sandbox - not a replacement for reinforcement
learning and not a global or universal claim.
"""
from __future__ import annotations

from .classification import (
    GATE_PASS_STATEMENT, FollowupMetrics, GateCondition,
    aggregate, all_followup_text, classify_corpus,
    followup_forbidden_hits, gate_conditions,
    gate_failing_conditions, gate_passes_all, replay_stability,
    technical_grounding,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GROUNDED, VERDICT_HALT,
    VERDICT_NOT_READY, V234Report,
    build_followup_verdict_artifact, build_go_no_go,
    build_paper_v2, build_report,
)
from .taxonomy import (
    FOLLOWUP_CLASSES, FollowupClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "FOLLOWUP_CLASSES",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_GROUNDED",
    "VERDICT_HALT",
    "VERDICT_NOT_READY",
    "FollowupClass",
    "FollowupMetrics",
    "GateCondition",
    "V234Report",
    "aggregate",
    "all_followup_text",
    "build_followup_verdict_artifact",
    "build_go_no_go",
    "build_paper_v2",
    "build_report",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "followup_forbidden_hits",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "is_acceptable",
    "replay_stability",
    "technical_grounding",
]
