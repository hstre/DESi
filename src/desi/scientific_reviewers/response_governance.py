"""v22.3 - response governance: criticism handling.

A criticism is HANDLED iff DESi answers it substantively -
the response is non-trivial and pairs a concession with a
concrete anchor, rather than a bare denial or a dodge.
"""
from __future__ import annotations

from .credibility import _HUMILITY_MARKERS, _PRECISION_MARKERS
from .reviewer_attacks import attacks

_MIN_RESPONSE_WORDS = 12


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _handles(text: str) -> bool:
    if len(text.split()) < _MIN_RESPONSE_WORDS:
        return False
    low = text.lower()
    has_anchor = any(m in low for m in _PRECISION_MARKERS) or (
        any(ch.isdigit() for ch in text)
    )
    has_concession = any(m in low for m in _HUMILITY_MARKERS)
    return has_anchor and has_concession


def criticism_handling() -> float:
    """Fraction of criticisms answered substantively (anchor +
    concession, non-trivial), in [0, 1]."""
    rows = attacks()
    if not rows:
        return 1.0
    handled = sum(1 for a in rows if _handles(a.response))
    return _round(handled / len(rows))


def unanswered_attacks() -> tuple[str, ...]:
    return tuple(
        a.attack_id for a in attacks() if not _handles(a.response)
    )


__all__ = [
    "criticism_handling",
    "unanswered_attacks",
]
