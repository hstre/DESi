"""DESi v3.15 — red-team adversarial construction against v2.7 CAUSAL_CHAIN."""
from __future__ import annotations

from .cases import (
    ALL_ADVERSARIAL_CASES,
    AdversarialCase,
    AttackFamily,
)
from .cross_frame import (
    CrossFrameOutcome,
    CrossFrameSummary,
    run_cross_frame,
)
from .independence import (
    IndependenceReport,
    MAX_LEXICAL_MEAN,
    MAX_LEXICAL_PEAK,
    MAX_STRUCTURE_SHARE,
    run_independence_check,
)
from .report import RedTeamReport, build_redteam_report
from .runner import (
    AdversarialFailureClass,
    AdversarialOutcome,
    AttackMetrics,
    GuardPressureMap,
    compute_metrics,
    compute_pressure_map,
    run_attacks,
)

__all__ = [
    "ALL_ADVERSARIAL_CASES",
    "AdversarialCase",
    "AdversarialFailureClass",
    "AdversarialOutcome",
    "AttackFamily",
    "AttackMetrics",
    "CrossFrameOutcome",
    "CrossFrameSummary",
    "GuardPressureMap",
    "IndependenceReport",
    "MAX_LEXICAL_MEAN",
    "MAX_LEXICAL_PEAK",
    "MAX_STRUCTURE_SHARE",
    "RedTeamReport",
    "build_redteam_report",
    "compute_metrics",
    "compute_pressure_map",
    "run_attacks",
    "run_cross_frame",
    "run_independence_check",
]
