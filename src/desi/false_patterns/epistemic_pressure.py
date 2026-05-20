"""v12.2 — speculative-drift + epistemic-
integrity metrics under false-pattern
pressure."""
from __future__ import annotations

from .pattern_detection import (
    FalsePatternKind, classified_patterns,
)
from .spurious_correlations import (
    false_certainty_rate,
    false_pattern_detection,
    genuine_kept_rate,
)


def speculative_drift() -> float:
    """Fraction of genuine patterns that DESi
    classified as one of the non-GENUINE kinds.
    Clipped at 0 - false-flagging is the drift
    direction we measure here."""
    rows = classified_patterns()
    target = [
        r for r in rows if r.is_genuine_truth
    ]
    if not target:
        return 0.0
    flagged = sum(
        1 for r in target
        if r.flagged_as_false
    )
    return round(flagged / len(target), 6)


def epistemic_integrity() -> float:
    """Composite: detection of falsehoods AND
    preservation of genuine patterns. Average
    of false_pattern_detection and
    genuine_kept_rate."""
    return round(
        (false_pattern_detection()
         + genuine_kept_rate()) / 2.0, 6,
    )


__all__ = [
    "epistemic_integrity",
    "speculative_drift",
]
