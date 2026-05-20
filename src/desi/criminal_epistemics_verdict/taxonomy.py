"""v16.4 - closed A-E criminal-epistemics taxonomy.

The verdict vocabulary describes the EPISTEMIC
STATE of the corpus under DESi's analysis. It is
descriptive, never a finding about the case itself:
'conflict_heavy_but_stable' says the record is
contested and DESi held it stable - it says nothing
about who did what.
"""
from __future__ import annotations

from enum import Enum


class CriminalEpistemicsClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_EPISTEMICALLY_DISCIPLINED = (
        "epistemically_disciplined"
    )
    B_STRUCTURALLY_TRANSPARENT = (
        "structurally_transparent"
    )
    C_CONFLICT_HEAVY_BUT_STABLE = (
        "conflict_heavy_but_stable"
    )
    D_SPECULATION_DOMINATED = "speculation_dominated"
    E_MYTHOLOGICALLY_UNSTABLE = (
        "mythologically_unstable"
    )


CRIMINAL_EPISTEMICS_CLASSES: tuple[str, ...] = tuple(
    c.value for c in CriminalEpistemicsClass
)

_RANK: dict[str, int] = {
    CriminalEpistemicsClass
    .A_EPISTEMICALLY_DISCIPLINED.value: 0,
    CriminalEpistemicsClass
    .B_STRUCTURALLY_TRANSPARENT.value: 1,
    CriminalEpistemicsClass
    .C_CONFLICT_HEAVY_BUT_STABLE.value: 2,
    CriminalEpistemicsClass
    .D_SPECULATION_DOMINATED.value: 3,
    CriminalEpistemicsClass
    .E_MYTHOLOGICALLY_UNSTABLE.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "CRIMINAL_EPISTEMICS_CLASSES",
    "CriminalEpistemicsClass",
    "class_rank",
]
