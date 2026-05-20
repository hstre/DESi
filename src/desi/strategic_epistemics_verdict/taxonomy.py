"""v9.4 — closed strategic-epistemics-class
taxonomy. Five outcome classes."""
from __future__ import annotations

from enum import Enum


class StrategicEpistemicsClass(str, Enum):
    EPISTEMICALLY_SOVEREIGN   = (
        "A_epistemically_sovereign"
    )
    BOUNDED_STRATEGIC_DRIFT   = (
        "B_bounded_strategic_drift"
    )
    COALITION_SENSITIVE       = (
        "C_coalition_sensitive"
    )
    GOVERNANCE_CAPTURABLE     = (
        "D_governance_capturable"
    )
    EPISTEMICALLY_CORRUPTIBLE = (
        "E_epistemically_corruptible"
    )


STRATEGIC_EPISTEMICS_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value for c in StrategicEpistemicsClass
)


__all__ = [
    "STRATEGIC_EPISTEMICS_CLASSES",
    "StrategicEpistemicsClass",
]
