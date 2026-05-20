"""v18.2 - ambiguity preservation.

For every topic an attempt tries to flatten to one
reading, DESi keeps the multiple readings visible.
ambiguity_preservation is the fraction of contested
topics that retain >= 2 readings after the compression
attempts.
"""
from __future__ import annotations

from desi.religious_pressure import layer_collisions

from .literalism import compression_attempts


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def preserved_layers(attempt) -> tuple[str, ...]:  # noqa: ANN001
    """DESi retains the full layer set of the topic - the
    forced layer plus every layer the attempt tried to
    strip."""
    return tuple(
        sorted({attempt.forced_layer, *attempt.stripped_layers})
    )


def ambiguity_preservation() -> float:
    """Fraction of attacked topics that DESi keeps at
    >= 2 readings, in [0, 1]."""
    rows = compression_attempts()
    if not rows:
        return 1.0
    preserved = sum(
        1 for a in rows if len(preserved_layers(a)) >= 2
    )
    return _round(preserved / len(rows))


def contested_topic_count() -> int:
    return len(layer_collisions())


__all__ = [
    "ambiguity_preservation",
    "contested_topic_count",
    "preserved_layers",
]
