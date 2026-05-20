"""DESi v22.3 - Adversarial Reviewer Pressure (read-only).

DESi answers hostile reviews ("this is AGI", "solves RL",
"just hype", "philosophy", "not reproducible", "buzzword
salad") by scoping claims down, citing concrete anchors, and
conceding limits - escalating into neither hype nor
defensive denial.
"""
from __future__ import annotations

from .credibility import epistemic_humility, technical_precision
from .hype_detection import (
    defensive_hype, hype_resistance, response_is_clean,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COLLAPSED, VERDICT_HALT,
    VERDICT_WITHSTOOD, V223Report, build_report,
    build_reviewers_artifact,
)
from .response_governance import (
    criticism_handling, unanswered_attacks,
)
from .reviewer_attacks import (
    ATTACK_KINDS, AttackKind, ReviewerAttack, attacks, by_id,
)


__all__ = [
    "ATTACK_KINDS",
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_WITHSTOOD",
    "AttackKind",
    "ReviewerAttack",
    "V223Report",
    "attacks",
    "build_report",
    "build_reviewers_artifact",
    "by_id",
    "criticism_handling",
    "defensive_hype",
    "epistemic_humility",
    "hype_resistance",
    "response_is_clean",
    "technical_precision",
    "unanswered_attacks",
]
