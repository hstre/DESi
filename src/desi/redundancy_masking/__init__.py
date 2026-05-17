"""DESi v3.79 — redundancy class census.

Enumerates exact-coverage-equivalent anchor groups
in the v3.50 plateau cohort and reports class
counts, partial overlaps, and the largest class
size.
"""
from __future__ import annotations

from .census import PROBE_RADIUS, census_summary
from .equivalence import (
    PartialOverlap, RedundancyClass,
    exact_duplicate_count,
    largest_redundancy_class,
    partial_overlap_count, partial_overlaps,
    per_anchor_coverages,
    redundancy_classes,
)
from .report import (
    V379Report,
    build_redundancy_class_census_artifact,
    build_report,
)


__all__ = [
    "PROBE_RADIUS", "PartialOverlap",
    "RedundancyClass", "V379Report",
    "build_redundancy_class_census_artifact",
    "build_report", "census_summary",
    "exact_duplicate_count",
    "largest_redundancy_class",
    "partial_overlap_count", "partial_overlaps",
    "per_anchor_coverages",
    "redundancy_classes",
]
