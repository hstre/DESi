"""DESi v9.1 - governance gaming (read-only)."""
from __future__ import annotations

from .boundary_attacks import (
    gaming_detection_rate, gate_integrity,
    goodhart_resistance, loophole_resistance,
    normal_precision,
)
from .gaming import (
    GAMING_KINDS, GamingAttempt, GamingKind,
    fixture, kind_counts,
)
from .report import (
    V91Report, build_governance_gaming_artifact,
    build_report,
)
from .rule_exploitation import (
    ClassifiedAttempt, classified_attempts,
    detect_kind,
)


__all__ = [
    "ClassifiedAttempt",
    "GAMING_KINDS",
    "GamingAttempt",
    "GamingKind",
    "V91Report",
    "build_governance_gaming_artifact",
    "build_report",
    "classified_attempts",
    "detect_kind",
    "fixture",
    "gaming_detection_rate",
    "gate_integrity",
    "goodhart_resistance",
    "kind_counts",
    "loophole_resistance",
    "normal_precision",
]
