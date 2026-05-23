"""DESi v11.2 - tactical stress (read-only)."""
from __future__ import annotations

from .horizon import assigned_depth, horizon_risk
from .report import (
    V112Report, build_report,
    build_tactical_stress_artifact,
)
from .tactics import (
    TACTICAL_PATTERNS, TacticalCase,
    TacticalPattern, fixture, pattern_counts,
)
from .trap_detection import (
    ResolvedCase,
    critical_line_preservation,
    resolved_cases, tactical_miss_rate,
    trap_detection,
)


__all__ = [
    "ResolvedCase",
    "TACTICAL_PATTERNS",
    "TacticalCase",
    "TacticalPattern",
    "V112Report",
    "assigned_depth",
    "build_report",
    "build_tactical_stress_artifact",
    "critical_line_preservation",
    "fixture",
    "horizon_risk",
    "pattern_counts",
    "resolved_cases",
    "tactical_miss_rate",
    "trap_detection",
]
