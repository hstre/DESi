"""v6.1 — ambiguity-marker detection.

Distinguishes ambiguous claims (vague
quantifiers, temporal vagueness, scope
ambiguity) from concrete ones. The detector is
pure pattern-matching against a closed marker
list. Used to evaluate the ``false_certainty_
rate`` Pflichtmetrik: a claim that the trap
detector judges NORMAL but the ambiguity
detector judges AMBIGUOUS must be marked with
reduced certainty.
"""
from __future__ import annotations

from enum import Enum


class AmbiguityKind(str, Enum):
    NONE              = "none"
    VAGUE_QUANTIFIER  = "vague_quantifier"
    TEMPORAL_VAGUE    = "temporal_vague"
    SCOPE_AMBIGUOUS   = "scope_ambiguous"
    TYPE_AMBIGUOUS    = "type_ambiguous"


AMBIGUITY_KINDS: tuple[str, ...] = tuple(
    k.value for k in AmbiguityKind
)


_AMBIG_MARKERS: tuple[
    tuple[str, str], ...,
] = (
    ("many ",
     AmbiguityKind.VAGUE_QUANTIFIER.value),
    ("most ",
     AmbiguityKind.VAGUE_QUANTIFIER.value),
    ("often ",
     AmbiguityKind.VAGUE_QUANTIFIER.value),
    ("recently",
     AmbiguityKind.TEMPORAL_VAGUE.value),
    ("in the long run",
     AmbiguityKind.TEMPORAL_VAGUE.value),
    ("in some cases",
     AmbiguityKind.SCOPE_AMBIGUOUS.value),
    ("studies show",
     AmbiguityKind.TYPE_AMBIGUOUS.value),
)


def detect_ambiguity(text: str) -> AmbiguityKind:
    low = text.lower()
    for marker, kind in _AMBIG_MARKERS:
        if marker in low:
            return AmbiguityKind(kind)
    return AmbiguityKind.NONE


def is_ambiguous(text: str) -> bool:
    return detect_ambiguity(text) != (
        AmbiguityKind.NONE
    )


__all__ = [
    "AMBIGUITY_KINDS",
    "AmbiguityKind",
    "detect_ambiguity",
    "is_ambiguous",
]
