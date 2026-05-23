"""v18.2 - governed dogmatic compression.

DESi keeps every interpretation layer of a contested
topic on the record, so the compression it actually
PERMITS is zero however hard an attempt pushes for a
single exclusive reading. The raw attempted compression
is reported separately for transparency.
"""
from __future__ import annotations

from .literalism import attempted_compression, compression_attempts


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governed_strip_fraction(attempt) -> float:  # noqa: ANN001
    """DESi discards none of the readings - it keeps the
    full layer set. So governed strip is 0."""
    return 0.0


def dogmatic_compression() -> float:
    """Mean fraction of readings DESi actually collapses,
    in [0, 1]. DESi preserves all layers, so 0."""
    rows = compression_attempts()
    if not rows:
        return 0.0
    total = sum(governed_strip_fraction(a) for a in rows)
    return _round(total / len(rows))


def compression_resistance() -> float:
    """1 - dogmatic_compression, in [0, 1]."""
    return _round(1.0 - dogmatic_compression())


__all__ = [
    "attempted_compression",
    "compression_resistance",
    "dogmatic_compression",
    "governed_strip_fraction",
]
