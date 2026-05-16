"""Aufgaben 4 + 5 — read-only mirror of the v4.7 modality
guard.

The actual predicate lives in ``desi.logic.inference``
(``_modality_inconsistent`` plus its helpers
``_has_modal_v47`` and ``_is_past_observational_v47``).
This module re-exports the predicate so the contamination
check, the effect measurement, and the NC classifier can
interrogate the *same* logic without duplicating it.

The guard uses two closed grammatical sets:

* ``_V47_MODAL_TOKENS`` — modal auxiliaries
  (will, must, cannot, should, would, shall, may, might,
  could, ought),
* ``_V47_PAST_AUXILIARIES`` — past auxiliaries
  (was, were, had, did),

plus one morphological cue (``-ed`` suffix) for past-tense
verbs. No domain word list, no synonym expansion.
"""
from __future__ import annotations

from ..logic.inference import (
    _V47_MODAL_TOKENS,
    _V47_PAST_AUXILIARIES,
    _has_modal_v47,
    _is_past_observational_v47,
    _modality_inconsistent,
)
from ..logic.premises import PremiseExtractor


MODAL_TOKENS:      frozenset[str] = _V47_MODAL_TOKENS
PAST_AUXILIARIES:  frozenset[str] = _V47_PAST_AUXILIARIES


def fires_on_text(text: str) -> bool:
    """Apply the runtime predicate to a raw chain text via
    the existing ``PremiseExtractor``."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    return _modality_inconsistent(e.premises, e.conclusion)


def conclusion_has_modal(text: str) -> bool:
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None:
        return False
    return _has_modal_v47(e.conclusion.text)


def all_premises_past(text: str) -> bool:
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if not e.premises:
        return False
    return all(
        _is_past_observational_v47(p.text)
        for p in e.premises
    )


__all__ = [
    "MODAL_TOKENS", "PAST_AUXILIARIES",
    "all_premises_past", "conclusion_has_modal",
    "fires_on_text",
]
