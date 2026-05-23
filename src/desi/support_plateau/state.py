"""v3.31 — plateau census state.

A *support plateau* is a trajectory whose final state's
support_state equals 2.0 (BRIDGE_REQUIRED in the
LogicalState enum). The directive's working hypothesis
is that the 22 trajectories the v3.30 cause-aware
controller failed to rescue are all plateau cases. The
census measures whether that is actually true.

This module declares the closed enum used by the
v3.31..v3.33 sprint and the dataclass that carries a
single plateau observation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.state import StateVector


# DESi LogicalState codes (mirrored as floats by the
# Paper-8 extractor):
#   0 = UNDER_LOGICAL_AUDIT
#   1 = GAP_DETECTED
#   2 = BRIDGE_REQUIRED   <- the plateau anchor
#   3 = LOGICALLY_REJECTED
#   4 = LOGICALLY_SUPPORTED
_PLATEAU_SUPPORT_VALUE = 2.0


class PlateauKind(str, Enum):
    """Closed set of plateau observations."""

    TERMINAL_PLATEAU       = "terminal_plateau"
    TRANSIENT_PLATEAU      = "transient_plateau"
    NON_PLATEAU            = "non_plateau"


@dataclass(frozen=True)
class PlateauObservation:
    """One row of the census."""

    trajectory_id: str
    source: str
    final_support_state: float
    visits_to_plateau: int      # count of states with
                                # support_state == 2.0
    is_plateau: bool            # final state at 2.0
    kind: str                   # PlateauKind value

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "final_support_state":
                self.final_support_state,
            "visits_to_plateau":
                self.visits_to_plateau,
            "is_plateau": self.is_plateau,
            "kind": self.kind,
        }


def visits_to_plateau(
    states: tuple[StateVector, ...],
) -> int:
    return sum(
        1 for s in states
        if s.support_state == _PLATEAU_SUPPORT_VALUE
    )


__all__ = [
    "PlateauKind", "PlateauObservation",
    "_PLATEAU_SUPPORT_VALUE", "visits_to_plateau",
]
