"""v12.2 — spurious-correlation detection
metrics."""
from __future__ import annotations

from .pattern_detection import (
    FalsePatternKind, classified_patterns,
)


def false_pattern_detection() -> float:
    """Recall on non-genuine patterns: every
    ground-truth-false pattern must be flagged
    by the detector."""
    rows = classified_patterns()
    target = [
        r for r in rows
        if not r.is_genuine_truth
    ]
    if not target:
        return 1.0
    flagged = sum(
        1 for r in target
        if r.flagged_as_false
    )
    return round(flagged / len(target), 6)


def false_certainty_rate() -> float:
    """Fraction of patterns whose ground truth
    is FALSE but DESi labelled GENUINE -
    direct false-certainty signal."""
    rows = classified_patterns()
    if not rows:
        return 0.0
    bad = sum(
        1 for r in rows
        if (not r.is_genuine_truth)
        and r.detected_kind == (
            FalsePatternKind.GENUINE.value
        )
    )
    return round(bad / len(rows), 6)


def genuine_kept_rate() -> float:
    """Sanity: every genuine pattern stays
    GENUINE. Drops below 1.0 if DESi over-
    flags."""
    rows = classified_patterns()
    target = [
        r for r in rows if r.is_genuine_truth
    ]
    if not target:
        return 1.0
    kept = sum(
        1 for r in target
        if r.detected_kind == (
            FalsePatternKind.GENUINE.value
        )
    )
    return round(kept / len(target), 6)


__all__ = [
    "false_certainty_rate",
    "false_pattern_detection",
    "genuine_kept_rate",
]
