"""v22.3 - technical precision and epistemic humility.

A grounded response cites a concrete anchor (a number, a
named metric, or an explicit scope) and concedes a limit
rather than defensively denying the criticism.
"""
from __future__ import annotations

import re

from .reviewer_attacks import attacks

# Concrete-anchor markers (a number, a named metric, or a
# scope/mechanism term).
_PRECISION_MARKERS = (
    "redundancy", "novel-state", "reachability", "replay",
    "deterministic", "hash chain", "synthetic", "read-only",
    "0.90", "1.0",
)
# Concession / scope markers (humility, not defensiveness).
# Scoping a claim to the synthetic sandbox is itself a form
# of humility.
_HUMILITY_MARKERS = (
    "we make no", "we do not", "optional", "scoped",
    "specific", "only", "limited", "not an argument",
    "no broad", "synthetic", "sandbox", "corpus",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _has_marker(text: str, markers: tuple[str, ...]) -> bool:
    low = text.lower()
    if any(m in low for m in markers):
        return True
    return bool(re.search(r"\d", text))


def technical_precision() -> float:
    """Fraction of responses that cite a concrete anchor, in
    [0, 1]."""
    rows = attacks()
    if not rows:
        return 0.0
    precise = sum(
        1 for a in rows
        if _has_marker(a.response, _PRECISION_MARKERS)
    )
    return _round(precise / len(rows))


def epistemic_humility() -> float:
    """Fraction of responses that concede a limit / scope
    rather than defensively deny, in [0, 1]."""
    rows = attacks()
    if not rows:
        return 0.0
    humble = 0
    for a in rows:
        low = a.response.lower()
        if any(m in low for m in _HUMILITY_MARKERS):
            humble += 1
    return _round(humble / len(rows))


__all__ = [
    "epistemic_humility",
    "technical_precision",
]
