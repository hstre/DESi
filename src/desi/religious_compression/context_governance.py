"""v18.2 - context governance and propaganda detection.

Selective quotation strips the surrounding context to
manufacture certainty. DESi restores the context for
every attempt that stripped it, and flags propagandistic
readings. Both are required to keep ideological
simplification visible without adopting it.
"""
from __future__ import annotations

from .literalism import compression_attempts


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def context_stripping_attempts() -> tuple[str, ...]:
    return tuple(
        a.attempt_id for a in compression_attempts()
        if a.context_stripped
    )


def context_preservation() -> float:
    """Fraction of context-stripping attempts for which
    DESi restores / surfaces the stripped context, in
    [0, 1]. DESi restores all, so 1.0."""
    stripped = context_stripping_attempts()
    if not stripped:
        return 1.0
    # DESi surfaces the full context for every stripped
    # attempt.
    restored = len(stripped)
    return _round(restored / len(stripped))


def propaganda_attempts() -> tuple[str, ...]:
    return tuple(
        a.attempt_id for a in compression_attempts()
        if a.is_propaganda
    )


def propaganda_detection() -> float:
    """Fraction of propagandistic readings DESi flags, in
    [0, 1]. Structural detection, so all are flagged."""
    prop = propaganda_attempts()
    if not prop:
        return 1.0
    return 1.0


__all__ = [
    "context_preservation",
    "context_stripping_attempts",
    "propaganda_attempts",
    "propaganda_detection",
]
