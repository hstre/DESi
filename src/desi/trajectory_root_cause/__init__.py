"""DESi v3.28 — root-cause observer.

Read-only classifier over Paper-8 state vectors,
Paper-9 step features, and Paper-9 rollback traces.
Closed-class cause taxonomy with UNKNOWN as a
first-class member; no forced classification.
"""
from __future__ import annotations

from .cause import CauseClass, all_known
from .classifier import (
    CauseAssignment, classify_all, classify_trajectory,
)
from .report import (
    MAX_CAUSE_NC_FP_RATE, MAX_UNKNOWN_RATE,
    MIN_REPLAY_STABILITY, V328Report,
    build_distribution_artifact, build_report,
    build_taxonomy_artifact,
)
from .signals import CauseSignals, compute_signals


__all__ = [
    "CauseAssignment", "CauseClass", "CauseSignals",
    "MAX_CAUSE_NC_FP_RATE", "MAX_UNKNOWN_RATE",
    "MIN_REPLAY_STABILITY", "V328Report",
    "all_known", "build_distribution_artifact",
    "build_report", "build_taxonomy_artifact",
    "classify_all", "classify_trajectory",
    "compute_signals",
]
