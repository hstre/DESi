"""DESi v3.35 — plateau cross-class transfer probe."""
from __future__ import annotations

from .report import (
    MIN_SPECIFICITY_SCORE, V335Report, build_report,
    build_specificity_artifact,
)
from .transfer import (
    CrossClassOutcome, TargetClass, collect_universe,
    per_class_counts, run_one,
)


__all__ = [
    "CrossClassOutcome", "MIN_SPECIFICITY_SCORE",
    "TargetClass", "V335Report", "build_report",
    "build_specificity_artifact", "collect_universe",
    "per_class_counts", "run_one",
]
