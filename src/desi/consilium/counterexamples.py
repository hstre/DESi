"""Closed libraries the SKEPTIC and DOMAIN_EXAMINER consult.

Both libraries are intentionally narrow and *pattern-based*. The
adversarial-counterexample matcher (``find_counterexample``)
recognises a small set of "exposure vs shelter" oppositions; the
metaphor library recognises a small set of (context, vocabulary)
pairs where the same word carries different meanings.

Authority-independence: neither library inspects author, title,
source, citation count, or reputation. The matchers see only the
bridge text + an explicitly-provided context tag + explicit
adversarial conditions. Adding a new pattern is a code edit and is
therefore an audit event.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Counterexample library — SKEPTIC consults this.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CounterexampleHit:
    """One adversarial condition the SKEPTIC could not resolve.

    ``opposing_concept`` is the bridge's claim that the condition
    negates. ``condition`` is the verbatim adversarial input that
    the caller supplied.
    """

    opposing_concept: str
    condition: str
    pattern: str


# Each entry maps a "bridge concept" pattern → a tuple of negator
# patterns. When the bridge contains the concept AND any additional
# condition contains a negator, a counterexample is registered.
_COUNTEREXAMPLES: dict[str, tuple[str, ...]] = {
    # Exposure / shelter
    "exposed to": ("has a roof", "is sheltered", "is covered",
                    "is under cover", "is indoor", "is enclosed"),
    "exposed to the rain": ("has a roof", "is sheltered",
                              "is covered", "is under cover"),
    # Visibility / opacity
    "visible from": ("is hidden by", "is occluded by",
                      "is concealed by"),
    # Reachability
    "accessible from": ("is sealed", "is locked",
                          "is blocked off"),
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".")


def find_counterexample(
    bridge_text: str,
    additional_conditions: tuple[str, ...],
) -> CounterexampleHit | None:
    """Return the first counterexample the SKEPTIC finds, or ``None``.

    Deterministic: same inputs → same hit. The first matching
    (concept, negator) pair wins; library iteration order is the
    insertion order in :data:`_COUNTEREXAMPLES`.
    """
    bridge_low = _normalise(bridge_text)
    for concept, negators in _COUNTEREXAMPLES.items():
        if concept not in bridge_low:
            continue
        for condition in additional_conditions:
            cond_low = _normalise(condition)
            for negator in negators:
                if negator in cond_low:
                    return CounterexampleHit(
                        opposing_concept=concept,
                        condition=condition,
                        pattern=negator,
                    )
    return None


# ---------------------------------------------------------------------------
# Metaphor library — DOMAIN_EXAMINER consults this.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetaphorHit:
    """A vocabulary word that is metaphorical in the given context."""

    context: str
    word: str
    note: str


_METAPHOR_LIBRARY: dict[str, dict[str, str]] = {
    "financial_newspaper": {
        "flooded": "in financial discourse 'flooded' typically means "
                    "saturated supply / capital inflow, not water",
        "crash":   "in financial discourse 'crash' typically means "
                    "a market collapse, not a physical impact",
        "bubble":  "in financial discourse 'bubble' is metaphorical "
                    "for over-priced markets",
        "boom":    "in financial discourse 'boom' is a metaphor for "
                    "sustained rapid growth",
    },
    "sports_journalism": {
        "flooded": "in sports discourse 'flooded' often describes a "
                    "midfield being overwhelmed by opponents",
        "killed":  "in sports discourse 'killed' is metaphor for a "
                    "decisive defeat",
    },
}


def supported_contexts() -> tuple[str, ...]:
    """Closed list of metaphor-aware contexts the v1.3 library knows."""
    return tuple(sorted(_METAPHOR_LIBRARY.keys()))


def find_metaphor(
    text: str,
    context: str,
) -> MetaphorHit | None:
    """Return the first metaphor hit, or ``None``."""
    if not context:
        return None
    vocab = _METAPHOR_LIBRARY.get(context)
    if vocab is None:
        return None
    low = _normalise(text)
    for word, note in vocab.items():
        if re.search(rf"\b{re.escape(word)}\b", low):
            return MetaphorHit(context=context, word=word, note=note)
    return None


__all__ = [
    "CounterexampleHit",
    "MetaphorHit",
    "find_counterexample",
    "find_metaphor",
    "supported_contexts",
]
