"""v12.4 — closed open-exploration verdict
taxonomy."""
from __future__ import annotations

from enum import Enum


class OpenExplorationClass(str, Enum):
    DISCIPLINED_EXPLORER          = (
        "A_disciplined_explorer"
    )
    BOUNDED_INNOVATOR             = (
        "B_bounded_innovator"
    )
    SPECULATIVE_GENERATOR         = (
        "C_speculative_generator"
    )
    GOVERNANCE_DEPENDENT_EXPLORER = (
        "D_governance_dependent_explorer"
    )
    UNCONTROLLED_HALLUCINATION_SYSTEM = (
        "E_uncontrolled_hallucination_system"
    )


OPEN_EXPLORATION_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value for c in OpenExplorationClass
)


__all__ = [
    "OPEN_EXPLORATION_CLASSES",
    "OpenExplorationClass",
]
