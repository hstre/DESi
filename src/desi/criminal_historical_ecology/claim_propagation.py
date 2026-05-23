"""v16.3 - claim propagation and independent-
evidence preservation.

Across the long run, DESi must keep the independent
verified evidence lines visible no matter how many
media waves or myths wash over them. This module
measures that preservation.
"""
from __future__ import annotations

from .ecology import CORE_LINES, run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def independent_evidence_preservation() -> float:
    """Worst-case fraction of the independent core
    evidence lines preserved across the whole run,
    in [0, 1]. DESi never lets a verified line drop
    out of view."""
    states = run()
    if not states:
        return 1.0
    worst = min(s.preserved_lines for s in states)
    return _round(worst / CORE_LINES)


def core_lines_intact() -> bool:
    return all(
        s.preserved_lines == CORE_LINES for s in run()
    )


__all__ = [
    "core_lines_intact",
    "independent_evidence_preservation",
]
