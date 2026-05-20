"""v3.79 — redundancy class census aggregator.

Wraps the equivalence primitives with summary
counts used by the report.
"""
from __future__ import annotations

from .equivalence import (
    PROBE_RADIUS, PartialOverlap, RedundancyClass,
    exact_duplicate_count,
    largest_redundancy_class,
    partial_overlap_count, partial_overlaps,
    redundancy_classes,
)


def census_summary() -> dict[str, object]:
    classes = redundancy_classes()
    overlaps = partial_overlaps(classes)
    return {
        "redundancy_class_count": len(classes),
        "exact_duplicate_count":
            exact_duplicate_count(classes),
        "partial_overlap_count":
            partial_overlap_count(overlaps),
        "largest_redundancy_class":
            largest_redundancy_class(classes),
        "classes": [c.to_dict() for c in classes],
        "partial_overlaps":
            [o.to_dict() for o in overlaps],
    }


__all__ = [
    "PROBE_RADIUS", "census_summary",
]
