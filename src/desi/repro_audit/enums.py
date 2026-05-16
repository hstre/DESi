"""Closed taxonomies for v4.11 — reproducibility class +
recommendation outcome."""
from __future__ import annotations

from enum import Enum


class ReproducibilityClass(str, Enum):
    """Closed reproducibility taxonomy (Aufgabe 4). Every
    artifact / test path receives exactly one of these
    values."""

    FROZEN_ARTIFACT_REPLAYABLE = "FROZEN_ARTIFACT_REPLAYABLE"
    LIVE_REPLAY_STABLE         = "LIVE_REPLAY_STABLE"
    ENVIRONMENT_DEPENDENT      = "ENVIRONMENT_DEPENDENT"
    HISTORICAL_RUNTIME_DRIFT   = "HISTORICAL_RUNTIME_DRIFT"
    NON_REPLAYABLE_BY_DESIGN   = "NON_REPLAYABLE_BY_DESIGN"
    UNKNOWN                    = "UNKNOWN"


class ToolReproPolicy(str, Enum):
    ENVIRONMENT_CONDITIONAL    = "ENVIRONMENT_CONDITIONAL"
    SIMULATED_MISSING_DEPENDENCY = "SIMULATED_MISSING_DEPENDENCY"


class RecommendationOutcome(str, Enum):
    CONFIRMED = "REPRO_HARDENING_CONFIRMED"
    PARTIAL   = "REPRO_HARDENING_PARTIAL"
    FAILED    = "REPRO_HARDENING_FAILED"
    NONE      = "NONE"


__all__ = [
    "RecommendationOutcome", "ReproducibilityClass",
    "ToolReproPolicy",
]
