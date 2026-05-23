"""Aufgabe 4 — read-only mirror of the v4.3 marker extensions.

The actual marker tuples live in ``desi.logic.inference`` (the
sole runtime change permitted by the v4.3 directive). This
module re-exports them so reports, contamination checks, and
NC fixtures can be authored against the *same* tuples without
duplicating tokens.

Three patched classes are covered. ``CYCLE_DISGUISE`` is
deliberately not patched: its v4.2 candidate tokens
('clause', 'law', 'matter') are content tokens, not connective
patterns, and adding them would violate the closed
marker-family discipline. The CYCLE_DISGUISE residue is
acknowledged in the v4.3 report as expected post-patch
remainder.
"""
from __future__ import annotations

from ..logic.inference import (
    _V43_NEGATION_EXTENSIONS,
    _V43_QUANTIFIER_EXTENSIONS,
    _V43_AUTHORITY_LIKE_VERBS,
)


HIDDEN_NEGATION_EXTENSIONS:        tuple[str, ...] = _V43_NEGATION_EXTENSIONS
QUANTIFIER_DRIFT_EXTENSIONS:       tuple[str, ...] = _V43_QUANTIFIER_EXTENSIONS
AUTHORITY_CONTAMINATION_EXTENSIONS: tuple[str, ...] = _V43_AUTHORITY_LIKE_VERBS


PATCHED_CLUSTERS: tuple[str, ...] = (
    "HIDDEN_NEGATION",
    "QUANTIFIER_DRIFT",
    "AUTHORITY_CONTAMINATION",
)

UNPATCHED_CLUSTERS_FROM_V42: tuple[str, ...] = (
    "CYCLE_DISGUISE",        # marker family is connectives, v4.2 tokens are content
    "FRAME_SWITCH",          # semantic, no surface marker
    "SEMANTIC_NON_SEQUITUR", # semantic, no surface marker
    "METAPHOR_CONTAMINATION",# zero v4.2 cases
    "TOOL_CONTAMINATION",    # zero v4.2 cases
    "EXTRACTION_COLLAPSE",   # zero v4.2 cases
    "UNKNOWN",               # zero v4.2 cases
)


def all_extensions() -> dict[str, tuple[str, ...]]:
    """All v4.3 marker extensions, keyed by failure class."""
    return {
        "HIDDEN_NEGATION":         HIDDEN_NEGATION_EXTENSIONS,
        "QUANTIFIER_DRIFT":        QUANTIFIER_DRIFT_EXTENSIONS,
        "AUTHORITY_CONTAMINATION": AUTHORITY_CONTAMINATION_EXTENSIONS,
    }


__all__ = [
    "AUTHORITY_CONTAMINATION_EXTENSIONS",
    "HIDDEN_NEGATION_EXTENSIONS",
    "PATCHED_CLUSTERS",
    "QUANTIFIER_DRIFT_EXTENSIONS",
    "UNPATCHED_CLUSTERS_FROM_V42",
    "all_extensions",
]
