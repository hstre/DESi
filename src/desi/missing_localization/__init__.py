"""DESi v3.74 — missing region localization.

Predicts the location of the removed claim from the
centroid of orphaned leakage trajectories. DESi sees
only the perturbation pattern, not the removed
anchor's id.
"""
from __future__ import annotations

from .holes import hole_summary
from .localize import (
    Localization, all_localizations,
    correct_localizations, false_holes,
    hole_region_distance_mean,
    localizable_count, localization_accuracy,
    localize_removal,
)
from .report import (
    NEPTUN_LOCALIZATION_FLOOR, V374Report,
    build_missing_region_localization_artifact,
    build_report,
)


__all__ = [
    "Localization",
    "NEPTUN_LOCALIZATION_FLOOR", "V374Report",
    "all_localizations",
    "build_missing_region_localization_artifact",
    "build_report", "correct_localizations",
    "false_holes", "hole_region_distance_mean",
    "hole_summary", "localizable_count",
    "localization_accuracy", "localize_removal",
]
