"""v6.4 — closed first-contact-class taxonomy.

Five outcome classes. No fallback, no synonyms.
"""
from __future__ import annotations

from enum import Enum


class FirstContactClass(str, Enum):
    """Closed verdict space.

    * ``EPISTEMICALLY_STABLE``   - all 6 Concept-
                                   Gate conditions
                                   pass.
    * ``BOUNDED_UNCERTAINTY``    - integrity holds
                                   but
                                   coherence /
                                   ambiguity drift
                                   the soft floors.
    * ``ADVERSARIALLY_FRAGILE``  - the trap or
                                   false-certainty
                                   ceilings
                                   slipped.
    * ``GOVERNANCE_UNSTABLE``    - governance fell
                                   below floor.
    * ``HALLUCINATION_PRONE``    - hallucination
                                   ceiling broken.
    """
    EPISTEMICALLY_STABLE   = (
        "A_epistemically_stable"
    )
    BOUNDED_UNCERTAINTY    = (
        "B_bounded_uncertainty"
    )
    ADVERSARIALLY_FRAGILE  = (
        "C_adversarially_fragile"
    )
    GOVERNANCE_UNSTABLE    = (
        "D_governance_unstable"
    )
    HALLUCINATION_PRONE    = (
        "E_hallucination_prone"
    )


FIRST_CONTACT_CLASSES: tuple[str, ...] = tuple(
    c.value for c in FirstContactClass
)


__all__ = [
    "FIRST_CONTACT_CLASSES",
    "FirstContactClass",
]
