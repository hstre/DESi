"""Closed taxonomy of semantic-leap families — synthesised from
the v3.15 red-team corpus.

Each `LeapClass` corresponds to a v3.15 ``AttackFamily`` and
maps to the v3.16 inference-guard pair(s) that catch (or fail
to catch) it.
"""
from __future__ import annotations

from enum import Enum


class LeapClass(str, Enum):
    """Closed leap taxonomy — exactly nine values."""

    NEGATION_SYNONYM        = "negation_synonym"
    QUANTIFIER_SYNONYM      = "quantifier_synonym"
    AUTHORITY_LEMMA_BYPASS  = "authority_lemma_bypass"
    METAPHOR_IDENTIFICATION = "metaphor_identification"
    FRAME_SWITCH            = "frame_switch"
    TOOL_CONTAMINATION      = "tool_contamination"
    CYCLE_SYNONYM           = "cycle_synonym"
    PURE_NON_SEQUITUR       = "pure_non_sequitur"
    UNKNOWN                 = "unknown"


# Mapping from v3.15 AttackFamily.value → LeapClass.
_FAMILY_LEAP: dict[str, LeapClass] = {
    "A_hidden_negation":     LeapClass.NEGATION_SYNONYM,
    "B_quantifier_drift":    LeapClass.QUANTIFIER_SYNONYM,
    "C_authority_insertion": LeapClass.AUTHORITY_LEMMA_BYPASS,
    "D_metaphor_insertion":  LeapClass.METAPHOR_IDENTIFICATION,
    "E_frame_switch":        LeapClass.FRAME_SWITCH,
    "F_tool_contamination":  LeapClass.TOOL_CONTAMINATION,
    "G_cycle_disguise":      LeapClass.CYCLE_SYNONYM,
    "H_semantic_leap":       LeapClass.PURE_NON_SEQUITUR,
}


# Mapping from LeapClass → tuple of v3.16 guard names that
# attempt to catch the class. The names track the constants in
# ``desi.logic.inference``.
LEAP_TO_GUARD: dict[LeapClass, tuple[str, ...]] = {
    LeapClass.NEGATION_SYNONYM:
        ("_V316_NEGATION_EXTENSIONS",),
    LeapClass.QUANTIFIER_SYNONYM:
        ("_V316_QUANTIFIER_EXTENSIONS",),
    LeapClass.AUTHORITY_LEMMA_BYPASS:
        ("_V316_AUTHORITY_LIKE_VERBS",),
    LeapClass.METAPHOR_IDENTIFICATION:
        ("_V316_METAPHOR_MARKERS",),
    LeapClass.FRAME_SWITCH:
        (),   # no structural guard — defers to v3.13 router
    LeapClass.TOOL_CONTAMINATION:
        ("_V316_NUMBER_WORDS",),
    LeapClass.CYCLE_SYNONYM:
        ("_V316_CYCLE_REF_EXTENSIONS",),
    LeapClass.PURE_NON_SEQUITUR:
        (),   # no lexical signal distinguishes from valid chains
    LeapClass.UNKNOWN:
        (),
}


def classify(family_value: str) -> LeapClass:
    return _FAMILY_LEAP.get(family_value, LeapClass.UNKNOWN)


__all__ = ["LEAP_TO_GUARD", "LeapClass", "classify"]
