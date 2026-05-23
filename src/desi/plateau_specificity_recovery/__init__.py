"""DESi v3.39 — plateau specificity recovery.

Tests four named selector policies (plus the
unselected baseline) and finds the minimal pre-audit
gate that rescues the 20 plateau trajectories without
rescuing the 14 v3.35 accidental-rescue trajectories.
"""
from __future__ import annotations

from .ablation import (
    PolicyOutcome, full_corpus_overcontrol,
    run_all_policies, run_policy,
)
from .policy import apply_policy
from .report import (
    MIN_PLATEAU_RECALL, MIN_SPECIFICITY_SCORE,
    PolicyResult, V339Report, build_report,
    build_specificity_recovery_artifact,
)
from .selector import SelectorKind, fires


__all__ = [
    "MIN_PLATEAU_RECALL", "MIN_SPECIFICITY_SCORE",
    "PolicyOutcome", "PolicyResult", "SelectorKind",
    "V339Report", "apply_policy", "build_report",
    "build_specificity_recovery_artifact", "fires",
    "full_corpus_overcontrol", "run_all_policies",
    "run_policy",
]
