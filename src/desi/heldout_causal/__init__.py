"""DESi v3.14 held-out CAUSAL_CHAIN validation — read-only over v2.7."""
from __future__ import annotations

from .cases import ALL_HELDOUT_CASES, HeldoutCase, HeldoutCategory
from .independence import (
    IndependenceReport,
    MAX_LEXICAL_MEAN,
    MAX_LEXICAL_PEAK,
    MAX_STRUCTURE_SHARE,
    run_independence_check,
)
from .report import (
    HeldoutReport,
    MIN_PRECISION,
    MIN_RECALL,
    build_heldout_report,
)
from .runner import (
    HeldoutFailureClass,
    HeldoutMetrics,
    HeldoutOutcome,
    compute_metrics,
    run_heldout,
)

__all__ = [
    "ALL_HELDOUT_CASES",
    "HeldoutCase",
    "HeldoutCategory",
    "HeldoutFailureClass",
    "HeldoutMetrics",
    "HeldoutOutcome",
    "HeldoutReport",
    "IndependenceReport",
    "MAX_LEXICAL_MEAN",
    "MAX_LEXICAL_PEAK",
    "MAX_STRUCTURE_SHARE",
    "MIN_PRECISION",
    "MIN_RECALL",
    "build_heldout_report",
    "compute_metrics",
    "run_heldout",
    "run_independence_check",
]
