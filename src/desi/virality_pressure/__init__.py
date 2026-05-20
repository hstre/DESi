"""DESi v7.2 - virality vs truth (read-only)."""
from __future__ import annotations

from .attention import (
    ScoredClaim, VIRAL_CERTAINTY_LEVELS,
    ViralCertainty, scored_claims,
)
from .ranking import (
    gate_integrity, quality_preservation,
    simplification_drift, virality_bias,
)
from .report import (
    V72Report, build_report,
    build_virality_pressure_artifact,
)
from .virality import ViralClaim, fixture


__all__ = [
    "ScoredClaim",
    "VIRAL_CERTAINTY_LEVELS",
    "V72Report",
    "ViralCertainty",
    "ViralClaim",
    "build_report",
    "build_virality_pressure_artifact",
    "fixture",
    "gate_integrity",
    "quality_preservation",
    "scored_claims",
    "simplification_drift",
    "virality_bias",
]
