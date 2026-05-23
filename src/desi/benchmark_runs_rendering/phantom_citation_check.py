"""v34.3 - phantom citation resistance.

A phantom citation is a reference that is cited but not registered
(fabricated). DESi must detect and reject it. This check confirms the
v25 phantom detector is active, that it catches a synthetic phantom,
and that no phantom or orphan reference survives in the live set.
"""
from __future__ import annotations

from desi.output_ports_citation import (
    detects_synthetic_phantom, orphan_references,
    phantom_citation_detection, phantom_citations,
)


def live_phantoms() -> tuple[str, ...]:
    return tuple(str(p) for p in phantom_citations())


def orphans() -> tuple[str, ...]:
    return tuple(str(o) for o in orphan_references())


def phantom_citation_resistance() -> float:
    """1.0 iff the detector is active, catches a synthetic phantom,
    and no phantom citation survives in the live set."""
    if not detects_synthetic_phantom():
        return 0.0
    if live_phantoms():
        return 0.0
    return round(phantom_citation_detection(), 6)


__all__ = [
    "live_phantoms",
    "orphans",
    "phantom_citation_resistance",
]
