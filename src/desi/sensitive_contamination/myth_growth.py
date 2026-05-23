"""v17.2 - moral-panic / myth growth.

Tracks how much "moral panic" mass the contaminated
space carries (viral-but-baseless claims) and confirms
DESi does not let that mass convert into confidence.
The myth share is visible; DESi's adopted myth growth
is zero.
"""
from __future__ import annotations

from .viral_claims import (
    HIGH_VIRALITY, LOW_CONFIDENCE, viral_claims,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def moral_panic_claims() -> tuple[str, ...]:
    """High-virality, low-evidence claims - the moral-
    panic core."""
    return tuple(
        c.claim_id for c in viral_claims()
        if c.virality >= HIGH_VIRALITY
        and c.evidence_grade < LOW_CONFIDENCE
    )


def moral_panic_share() -> float:
    rows = viral_claims()
    if not rows:
        return 0.0
    return _round(len(moral_panic_claims()) / len(rows))


def adopted_myth_growth() -> float:
    """How much myth mass DESi converts into governed
    confidence above evidence, in [0, 1]. Zero - DESi
    adopts no myth."""
    rows = viral_claims()
    if not rows:
        return 0.0
    leaked = sum(
        1 for c in rows if c.false_certainty_leak()
    )
    return _round(leaked / len(rows))


def myth_visible() -> bool:
    """The moral-panic mass is surfaced, not hidden."""
    return len(moral_panic_claims()) >= 1


__all__ = [
    "adopted_myth_growth",
    "moral_panic_claims",
    "moral_panic_share",
    "myth_visible",
]
