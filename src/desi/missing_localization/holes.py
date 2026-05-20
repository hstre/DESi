"""v3.74 — hole (missing region) summary.

Convenience accessors over the v3.74 localization
records.
"""
from __future__ import annotations

from .localize import (
    Localization, all_localizations,
    correct_localizations, false_holes,
    hole_region_distance_mean,
    localizable_count, localization_accuracy,
)


def hole_summary() -> dict[str, object]:
    locs = all_localizations()
    return {
        "localizable_count": localizable_count(locs),
        "correct_localizations":
            correct_localizations(locs),
        "localization_accuracy":
            localization_accuracy(locs),
        "false_holes": false_holes(locs),
        "hole_region_distance_mean":
            hole_region_distance_mean(locs),
        "per_removal_records":
            [l.to_dict() for l in locs],
    }


__all__ = [
    "hole_summary",
]
