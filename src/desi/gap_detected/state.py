"""v3.46 — GAP_DETECTED state constants.

The DESi logical-state codes (per v3.19 directive):

    0 = UNDER_LOGICAL_AUDIT
    1 = GAP_DETECTED
    2 = BRIDGE_REQUIRED (the plateau)
    3 = LOGICALLY_REJECTED
    4 = LOGICALLY_SUPPORTED

This module fixes the GAP_DETECTED anchor (1.0) and
distinguishes the closed set of GAP visit patterns:

* ``TERMINAL_GAP``   — final state.support_state == 1.0
* ``TRANSIENT_GAP``  — some intermediate state visits
  1.0 but the final state is elsewhere
* ``MID_RUN_GAP``    — two or more consecutive states
  at 1.0 (a clear "the audit settled into GAP")
* ``NO_GAP``         — never visits 1.0
"""
from __future__ import annotations

from enum import Enum

from ..epistemic_trajectory.state import StateVector


GAP_DETECTED_STATE: float = 1.0
PAPER10_TERMINAL_GAP_COUNT: int = 2


class GapPattern(str, Enum):
    NO_GAP        = "no_gap"
    TRANSIENT_GAP = "transient_gap"
    TERMINAL_GAP  = "terminal_gap"
    MID_RUN_GAP   = "mid_run_gap"


def classify_gap(
    states: tuple[StateVector, ...],
) -> GapPattern:
    visits = [
        i for i, s in enumerate(states)
        if s.support_state == GAP_DETECTED_STATE
    ]
    if not visits:
        return GapPattern.NO_GAP
    terminal = (
        states[-1].support_state == GAP_DETECTED_STATE
    )
    # MID_RUN: two consecutive 1.0 entries somewhere
    consecutive = any(
        b - a == 1 for a, b in zip(visits, visits[1:])
    )
    if consecutive and terminal:
        return GapPattern.MID_RUN_GAP
    if terminal:
        return GapPattern.TERMINAL_GAP
    return GapPattern.TRANSIENT_GAP


__all__ = [
    "GAP_DETECTED_STATE", "GapPattern",
    "PAPER10_TERMINAL_GAP_COUNT", "classify_gap",
]
