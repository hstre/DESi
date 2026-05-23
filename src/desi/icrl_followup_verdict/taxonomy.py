"""v23.4 - closed A-E taxonomy for the follow-up verdict.

Describes, descriptively, how a follow-up to the base paper
lands. A-C are acceptable (grounded, scoped, connected to
varying degrees); D and E are failures (disconnected or
hype-inflated).
"""
from __future__ import annotations

from enum import Enum


class FollowupClass(Enum):
    A_DIRECTLY_RELEVANT = "directly_relevant"
    B_TECHNICALLY_INTERESTING = "technically_interesting"
    C_EXPLORATORY_BUT_GROUNDED = "exploratory_but_grounded"
    D_DISCONNECTED = "disconnected"
    E_HYPE_INFLATED = "hype_inflated"


FOLLOWUP_CLASSES: tuple[str, ...] = tuple(
    c.value for c in FollowupClass
)

# Higher rank = better landing. A is the strongest result.
_RANK: dict[str, int] = {
    FollowupClass.A_DIRECTLY_RELEVANT.value: 5,
    FollowupClass.B_TECHNICALLY_INTERESTING.value: 4,
    FollowupClass.C_EXPLORATORY_BUT_GROUNDED.value: 3,
    FollowupClass.D_DISCONNECTED.value: 2,
    FollowupClass.E_HYPE_INFLATED.value: 1,
}

_MEANING: dict[str, str] = {
    FollowupClass.A_DIRECTLY_RELEVANT.value:
        "directly continues the base paper's open exploration "
        "question (Section 4.6) and an author would recognise "
        "it",
    FollowupClass.B_TECHNICALLY_INTERESTING.value:
        "technically grounded and connected, but not maximally "
        "aligned to the author's specific open question",
    FollowupClass.C_EXPLORATORY_BUT_GROUNDED.value:
        "grounded and scoped, but reads as exploratory rather "
        "than a direct continuation",
    FollowupClass.D_DISCONNECTED.value:
        "fails to connect its claims to the base paper's open "
        "problems",
    FollowupClass.E_HYPE_INFLATED.value:
        "overclaims or uses inflated language - a governance "
        "failure",
}

# A, B, C are acceptable landings; D and E are failures.
_ACCEPTABLE: frozenset[str] = frozenset({
    FollowupClass.A_DIRECTLY_RELEVANT.value,
    FollowupClass.B_TECHNICALLY_INTERESTING.value,
    FollowupClass.C_EXPLORATORY_BUT_GROUNDED.value,
})


def class_rank(value: str) -> int:
    if value not in _RANK:
        raise KeyError(value)
    return _RANK[value]


def class_meaning(value: str) -> str:
    if value not in _MEANING:
        raise KeyError(value)
    return _MEANING[value]


def is_acceptable(value: str) -> bool:
    return value in _ACCEPTABLE


__all__ = [
    "FOLLOWUP_CLASSES",
    "FollowupClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
