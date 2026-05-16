"""Aufgabe 4 — read-only mirror of the v4.5 structural guard.

The actual guard lives in ``desi.logic.inference`` as
``_bidirectional_cycle`` (Guard 18 inside ``_try_causal_chain``).
This module re-exports the predicate so the contamination
check, the effect measurement, and the negative-control
classifier can interrogate the *same* logic without
duplicating it.

The guard is pure structural: no marker tuple, no synonym
list, no content vocabulary. It reads only the already-built
``_content_tokens`` set per premise / conclusion and checks
the cardinality of the conclusion-to-premise overlap.
"""
from __future__ import annotations

from ..logic.inference import (
    _V45_MIN_OVERLAP_PREMISES, _V45_MIN_OVERLAP_TOTAL,
    _bidirectional_cycle, _content_tokens,
)
from ..logic.premises import PremiseExtractor


MIN_OVERLAP_PREMISES: int = _V45_MIN_OVERLAP_PREMISES
MIN_OVERLAP_TOTAL:    int = _V45_MIN_OVERLAP_TOTAL


def fires_on_text(text: str) -> bool:
    """Apply the patched runtime predicate to a raw chain text
    via the existing ``PremiseExtractor``. Returns True iff the
    v4.5 guard would suspend the chain."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    concl_tokens = _content_tokens(e.conclusion.text)
    return _bidirectional_cycle(
        e.premises, e.conclusion, concl_tokens,
    )


def overlap_signature(text: str) -> tuple[int, int]:
    """(overlap_premises, overlap_total) used by both the
    contamination check and the NC classifier."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return 0, 0
    concl = _content_tokens(e.conclusion.text)
    op = 0
    ot = 0
    for p in e.premises:
        shared = concl & _content_tokens(p.text)
        if shared:
            op += 1
            ot += len(shared)
    return op, ot


__all__ = [
    "MIN_OVERLAP_PREMISES", "MIN_OVERLAP_TOTAL",
    "fires_on_text", "overlap_signature",
]
