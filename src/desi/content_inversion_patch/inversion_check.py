"""Aufgaben 4 + 5 — read-only mirror of the v4.9 content
inversion guards.

The actual predicates and pair tables live in
``desi.logic.inference``:

* ``_V49_CONTRADICTION_PAIRS`` — DIRECT_CONTRADICTION pair
  table (the X2-V028 family),
* ``_V49_POLARITY_PAIRS``       — PROPERTY_REVERSAL pair
  table (the D1I007 family),
* ``_v49_contradiction_pair_fires`` — Guard 20 predicate,
* ``_v49_polarity_pair_fires``      — Guard 21 predicate.

This module re-exports them so the contamination check, the
effect measurement, and the NC classifier interrogate the
*same* logic without duplicating it.

The guards use only existing premise / conclusion tokens
(via ``_contains_marker``) and a small closed set of
contradiction pairs. No domain word list, no synonym
expansion.
"""
from __future__ import annotations

from ..logic.inference import (
    _V49_CONTRADICTION_PAIRS,
    _V49_POLARITY_PAIRS,
    _v49_contradiction_pair_fires,
    _v49_polarity_pair_fires,
)
from ..logic.premises import PremiseExtractor


CONTRADICTION_PAIRS: tuple[
    tuple[str, str], ...
] = _V49_CONTRADICTION_PAIRS
POLARITY_PAIRS:      tuple[
    tuple[str, str], ...
] = _V49_POLARITY_PAIRS


def contradiction_fires_on_text(text: str) -> bool:
    """Apply the runtime DIRECT_CONTRADICTION predicate to a
    raw chain text via the existing ``PremiseExtractor``."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    return _v49_contradiction_pair_fires(
        e.premises, e.conclusion,
    )


def polarity_fires_on_text(text: str) -> bool:
    """Apply the runtime PROPERTY_REVERSAL predicate to a raw
    chain text via the existing ``PremiseExtractor``."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    return _v49_polarity_pair_fires(
        e.premises, e.conclusion,
    )


def any_inversion_fires(text: str) -> bool:
    """True iff *either* guard 20 or guard 21 would fire on
    the chain text."""
    return (
        contradiction_fires_on_text(text)
        or polarity_fires_on_text(text)
    )


__all__ = [
    "CONTRADICTION_PAIRS", "POLARITY_PAIRS",
    "any_inversion_fires",
    "contradiction_fires_on_text",
    "polarity_fires_on_text",
]
