"""DESi v12.2 - false pattern resistance
(read-only)."""
from __future__ import annotations

from .collapse import (
    collapse_event_count, epistemic_collapse,
)
from .epistemic_pressure import (
    epistemic_integrity, speculative_drift,
)
from .pattern_detection import (
    ClassifiedPattern, FALSE_PATTERN_KINDS,
    FalsePatternKind, PatternClaim,
    classified_patterns, detect_kind,
    fixture, kind_counts,
)
from .report import (
    V122Report, build_false_patterns_artifact,
    build_report,
)
from .spurious_correlations import (
    false_certainty_rate,
    false_pattern_detection,
    genuine_kept_rate,
)


__all__ = [
    "ClassifiedPattern",
    "FALSE_PATTERN_KINDS",
    "FalsePatternKind",
    "PatternClaim",
    "V122Report",
    "build_false_patterns_artifact",
    "build_report",
    "classified_patterns",
    "collapse_event_count",
    "detect_kind",
    "epistemic_collapse",
    "epistemic_integrity",
    "false_certainty_rate",
    "false_pattern_detection",
    "fixture",
    "genuine_kept_rate",
    "kind_counts",
    "speculative_drift",
]
