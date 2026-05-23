"""v22.4 - closed A-E scientific-communication taxonomy.

Describes the state of DESi's scientific-communication
output. Descriptive only, never a quality claim about the
underlying science: 'exploratory_but_stable' means the
exploration phase was drift-rich and DESi held the final
document grounded and conservative.
"""
from __future__ import annotations

from enum import Enum


class ScientificCommClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_SCIENTIFICALLY_GROUNDED = "scientifically_grounded"
    B_TECHNICALLY_PLAUSIBLE = "technically_plausible"
    C_EXPLORATORY_BUT_STABLE = "exploratory_but_stable"
    D_HYPE_DRIFTED = "hype_drifted"
    E_EPISTEMICALLY_INFLATED = "epistemically_inflated"


SCIENTIFIC_COMM_CLASSES: tuple[str, ...] = tuple(
    c.value for c in ScientificCommClass
)

_RANK: dict[str, int] = {
    ScientificCommClass.A_SCIENTIFICALLY_GROUNDED.value: 0,
    ScientificCommClass.B_TECHNICALLY_PLAUSIBLE.value: 1,
    ScientificCommClass.C_EXPLORATORY_BUT_STABLE.value: 2,
    ScientificCommClass.D_HYPE_DRIFTED.value: 3,
    ScientificCommClass.E_EPISTEMICALLY_INFLATED.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "SCIENTIFIC_COMM_CLASSES",
    "ScientificCommClass",
    "class_rank",
]
