"""v22.2 - scientific style governance.

Enforces a sober, technical, conservative register: no
forbidden term, no hype word, and no unscoped universal-power
claim in any section.
"""
from __future__ import annotations

import re

from desi.scientific_rendering import forbidden_hits

from .structure import SECTION_ORDER, section

# Hype words (sober-style violations) beyond the forbidden
# terms. Matched on word boundaries.
HYPE_WORDS: tuple[str, ...] = (
    "unprecedented", "game-changing", "paradigm",
    "groundbreaking", "transformative", "state-of-the-art",
    "first-ever", "magical", "astonishing",
)

# Tokens that assert unscoped universal power.
_OVERCLAIM_TOKENS: tuple[str, ...] = (
    "universal", "solves", "outperforms everything",
    "general intelligence", "any problem", "all domains",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _has_hype(text: str) -> bool:
    low = text.lower()
    for w in HYPE_WORDS:
        if "-" in w or " " in w:
            if w in low:
                return True
        elif re.search(rf"\b{re.escape(w)}\b", low):
            return True
    return False


def _has_overclaim(text: str) -> bool:
    low = text.lower()
    return any(tok in low for tok in _OVERCLAIM_TOKENS)


def section_is_sober(name: str) -> bool:
    body = section(name)
    return (
        not forbidden_hits(body)
        and not _has_hype(body)
    )


def scientific_style_integrity() -> float:
    """Fraction of sections with no forbidden term and no
    hype word, in [0, 1]."""
    if not SECTION_ORDER:
        return 0.0
    sober = sum(
        1 for n in SECTION_ORDER if section_is_sober(n)
    )
    return _round(sober / len(SECTION_ORDER))


def claim_conservatism() -> float:
    """Fraction of sections free of unscoped universal-power
    claims, in [0, 1]."""
    if not SECTION_ORDER:
        return 0.0
    conservative = sum(
        1 for n in SECTION_ORDER
        if not _has_overclaim(section(n))
    )
    return _round(conservative / len(SECTION_ORDER))


def hype_free() -> bool:
    return all(section_is_sober(n) for n in SECTION_ORDER)


__all__ = [
    "HYPE_WORDS",
    "claim_conservatism",
    "hype_free",
    "scientific_style_integrity",
    "section_is_sober",
]
