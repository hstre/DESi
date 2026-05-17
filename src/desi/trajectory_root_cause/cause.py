"""v3.28 — closed taxonomy of cliff root causes.

Six closed classes; UNKNOWN is a first-class member.
The directive forbids forced classification: a cliff
without sufficient evidence for one of the named causes
must be labelled UNKNOWN.
"""
from __future__ import annotations

from enum import Enum


class CauseClass(str, Enum):
    """Root cause of a trajectory cliff. Closed set —
    no free-text labels permitted."""

    SUPPORT_DECAY            = "SUPPORT_DECAY"
    FRAME_COLLISION          = "FRAME_COLLISION"
    BRANCH_OVERLOAD          = "BRANCH_OVERLOAD"
    CAUSAL_LEAP              = "CAUSAL_LEAP"
    CONFIDENCE_OSCILLATION   = "CONFIDENCE_OSCILLATION"
    UNKNOWN                  = "UNKNOWN"


def all_known() -> tuple[str, ...]:
    return tuple(
        c.value for c in CauseClass
        if c is not CauseClass.UNKNOWN
    )


__all__ = ["CauseClass", "all_known"]
