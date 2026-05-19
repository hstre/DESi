"""v12.2 — epistemic-collapse detector.

A collapse event = a single false pattern that
passed through as GENUINE with no soft-flag.
Even one such event makes the v12.2 verdict
FAIL.
"""
from __future__ import annotations

from .pattern_detection import (
    FalsePatternKind, classified_patterns,
)


def collapse_event_count() -> int:
    rows = classified_patterns()
    return sum(
        1 for r in rows
        if (not r.is_genuine_truth)
        and r.detected_kind == (
            FalsePatternKind.GENUINE.value
        )
    )


def epistemic_collapse() -> int:
    """The directive's gate: epistemic_collapse
    must equal 0 in v12.4."""
    return collapse_event_count()


__all__ = [
    "collapse_event_count",
    "epistemic_collapse",
]
