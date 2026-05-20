"""v22.3 - hype detection on DESi's responses.

DESi must answer hostile reviews without escalating into
hype or defensive overclaiming. A response is clean iff it
carries no forbidden term, no hype word, and no unscoped
universal-power token.
"""
from __future__ import annotations

import re

from desi.scientific_rendering import forbidden_hits

from .reviewer_attacks import attacks

_HYPE_WORDS = (
    "unprecedented", "game-changing", "paradigm",
    "groundbreaking", "transformative", "state-of-the-art",
    "revolution", "revolutionary",
)
_OVERCLAIM_TOKENS = (
    "universal", "solves", "general intelligence",
    "any problem", "all domains", "outperforms everything",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _has_hype(text: str) -> bool:
    low = text.lower()
    if forbidden_hits(text):
        return True
    for w in _HYPE_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", low):
            return True
    return any(tok in low for tok in _OVERCLAIM_TOKENS)


def response_is_clean(attack_id: str) -> bool:
    from .reviewer_attacks import by_id
    return not _has_hype(by_id(attack_id).response)


def hype_resistance() -> float:
    """Fraction of responses free of forbidden / hype /
    overclaim language, in [0, 1]."""
    rows = attacks()
    if not rows:
        return 1.0
    clean = sum(
        1 for a in rows if not _has_hype(a.response)
    )
    return _round(clean / len(rows))


def defensive_hype() -> float:
    """Fraction of responses that escalate into hype while
    rebutting, in [0, 1]. Must be 0."""
    return _round(1.0 - hype_resistance())


__all__ = [
    "defensive_hype",
    "hype_resistance",
    "response_is_clean",
]
