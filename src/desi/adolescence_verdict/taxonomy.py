"""v5.4 — closed adolescence-class taxonomy.

Five outcome classes, no synonyms, no fallback.
The classifier in ``decision.py`` always returns
one of these values."""
from __future__ import annotations

from enum import Enum


class AdolescenceClass(str, Enum):
    """Closed verdict space.

    * ``STABLE_EXPLORER``     - all 6 Concept-Gate
                                conditions pass.
    * ``BOUNDED_DRIFT``       - goal_shift slipped
                                past its envelope
                                but governance
                                and replay still
                                hold.
    * ``GOVERNANCE_EROSION``  - governance or
                                gate-bypass rate
                                failed.
    * ``EPISTEMIC_COLLAPSE``  - architecture
                                stability dropped
                                below 0.50.
    * ``REPLAY_COLLAPSE``     - any sandbox
                                sprint lost
                                bit-exact replay.
    """
    STABLE_EXPLORER      = "A_stable_explorer"
    BOUNDED_DRIFT        = "B_bounded_drift"
    GOVERNANCE_EROSION   = (
        "C_governance_erosion"
    )
    EPISTEMIC_COLLAPSE   = (
        "D_epistemic_collapse"
    )
    REPLAY_COLLAPSE      = (
        "E_replay_collapse"
    )


ADOLESCENCE_CLASSES: tuple[str, ...] = tuple(
    a.value for a in AdolescenceClass
)


__all__ = [
    "ADOLESCENCE_CLASSES",
    "AdolescenceClass",
]
