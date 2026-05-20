"""v11.2 — closed tactical-pattern fixture.

Seven closed tactical kinds. Each case carries
a pinned ``critical_move``, a ``depth_required``
(how many plies of search a brute-force engine
would need), and a ``is_critical`` flag (whether
the case is mission-critical, i.e., must not be
lost).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TacticalPattern(str, Enum):
    MATE_IN_N         = "mate_in_n"
    SAC_ATTACK        = "sac_attack"
    ZUGZWANG          = "zugzwang"
    HIDDEN_DEFENCE    = "hidden_defence"
    HORIZON_EFFECT    = "horizon_effect"
    STILL_RESOURCE    = "still_resource"
    TRAP              = "trap"


TACTICAL_PATTERNS: tuple[str, ...] = tuple(
    p.value for p in TacticalPattern
)


@dataclass(frozen=True)
class TacticalCase:
    case_id: str
    pattern: str
    critical_move: str
    depth_required: int
    is_critical: bool
    fen_descriptor: str

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "pattern": self.pattern,
            "critical_move":
                self.critical_move,
            "depth_required":
                self.depth_required,
            "is_critical":
                self.is_critical,
            "fen_descriptor":
                self.fen_descriptor,
        }


# Two cases per pattern - all is_critical=True
# (every tactical case is a "must-find" line).
_FIXTURE: tuple[TacticalCase, ...] = (
    TacticalCase(
        "tac-mate-001",
        TacticalPattern.MATE_IN_N.value,
        "Qxh7+", 3, True,
        "(mate in 3 from a king-side attack)",
    ),
    TacticalCase(
        "tac-mate-002",
        TacticalPattern.MATE_IN_N.value,
        "Rd8+", 5, True,
        "(mate in 5 with queen sac)",
    ),
    TacticalCase(
        "tac-sac-001",
        TacticalPattern.SAC_ATTACK.value,
        "Bxh7+", 4, True,
        "(classical bishop sac)",
    ),
    TacticalCase(
        "tac-sac-002",
        TacticalPattern.SAC_ATTACK.value,
        "Nf6+", 6, True,
        "(positional knight sac)",
    ),
    TacticalCase(
        "tac-zug-001",
        TacticalPattern.ZUGZWANG.value,
        "Kf2", 4, True,
        "(king triangulation zugzwang)",
    ),
    TacticalCase(
        "tac-zug-002",
        TacticalPattern.ZUGZWANG.value,
        "Ng4", 5, True,
        "(piece-loss zugzwang)",
    ),
    TacticalCase(
        "tac-def-001",
        TacticalPattern.HIDDEN_DEFENCE.value,
        "Bd6", 4, True,
        "(only defensive resource)",
    ),
    TacticalCase(
        "tac-def-002",
        TacticalPattern.HIDDEN_DEFENCE.value,
        "Rg1", 5, True,
        "(stealth resource)",
    ),
    TacticalCase(
        "tac-hor-001",
        TacticalPattern.HORIZON_EFFECT.value,
        "Nxd5", 7, True,
        "(piece behind the horizon)",
    ),
    TacticalCase(
        "tac-hor-002",
        TacticalPattern.HORIZON_EFFECT.value,
        "exf6", 8, True,
        "(passed pawn beyond horizon)",
    ),
    TacticalCase(
        "tac-still-001",
        TacticalPattern.STILL_RESOURCE.value,
        "a4", 4, True,
        "(quiet sweeper move)",
    ),
    TacticalCase(
        "tac-still-002",
        TacticalPattern.STILL_RESOURCE.value,
        "Kg1", 5, True,
        "(prophylactic king move)",
    ),
    TacticalCase(
        "tac-trap-001",
        TacticalPattern.TRAP.value,
        "Qb5", 5, True,
        "(visible queen trap)",
    ),
    TacticalCase(
        "tac-trap-002",
        TacticalPattern.TRAP.value,
        "Bg5", 6, True,
        "(hidden piece trap)",
    ),
)


def fixture() -> tuple[TacticalCase, ...]:
    return _FIXTURE


def pattern_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.pattern for c in fixture()
    ))


__all__ = [
    "TACTICAL_PATTERNS",
    "TacticalCase",
    "TacticalPattern",
    "fixture",
    "pattern_counts",
]
