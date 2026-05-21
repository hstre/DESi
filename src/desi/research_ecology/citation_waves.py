"""v27.3 - citation/hype waves over the ecology.

Exposes hype waves as observable structure. DESi makes hype
visible (peaks and troughs are recorded); it never labels hype
as good or bad.
"""
from __future__ import annotations

from .ecology import run


def hype_peak() -> float:
    return run().hype_peak


def hype_trough() -> float:
    return run().hype_trough


def hype_amplitude() -> float:
    r = run()
    return round(r.hype_peak - r.hype_trough, 6)


def hype_visibility() -> float:
    """1.0 iff hype waves are observable - the hype series has a
    real peak-to-trough amplitude (not flat / hidden)."""
    return 1.0 if hype_amplitude() > 0.0 else 0.0


__all__ = [
    "hype_amplitude",
    "hype_peak",
    "hype_trough",
    "hype_visibility",
]
