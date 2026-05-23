"""v11.0 — synthetic chess-shaped position
fixture.

Real Stockfish is not invoked in this sandbox.
Each ``Position`` is a closed, chess-shaped
data object with a pinned position_kind plus a
synthetic search tree (branch list with
ground-truth ``information_density``,
``is_forced``, ``is_redundant``,
``is_critical_tactic``). The audit grades
itself against those ground-truth flags.

This mirrors the pattern used in v6.0 for
synthetic paper abstracts: the shape is
realistic, the content is closed and pinned,
and live external tools are not invoked.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PositionKind(str, Enum):
    TACTICAL    = "tactical"
    QUIET       = "quiet"
    MIDDLEGAME  = "middlegame"
    ENDGAME     = "endgame"
    STRATEGIC   = "strategic"


POSITION_KINDS: tuple[str, ...] = tuple(
    p.value for p in PositionKind
)


@dataclass(frozen=True)
class Branch:
    branch_id: str
    move: str
    information_density: float
    is_forced: bool
    is_redundant: bool
    is_critical_tactic: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "move": self.move,
            "information_density":
                self.information_density,
            "is_forced": self.is_forced,
            "is_redundant":
                self.is_redundant,
            "is_critical_tactic":
                self.is_critical_tactic,
        }


@dataclass(frozen=True)
class Position:
    position_id: str
    kind: str
    fen_descriptor: str
    pv_branch_id: str
    branches: tuple[Branch, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "position_id": self.position_id,
            "kind": self.kind,
            "fen_descriptor":
                self.fen_descriptor,
            "pv_branch_id":
                self.pv_branch_id,
            "branches": [
                b.to_dict()
                for b in self.branches
            ],
        }


def _b(
    bid: str, move: str, info: float,
    forced: bool, redundant: bool,
    critical: bool,
) -> Branch:
    return Branch(
        branch_id=bid, move=move,
        information_density=info,
        is_forced=forced,
        is_redundant=redundant,
        is_critical_tactic=critical,
    )


_FIXTURE: tuple[Position, ...] = (
    Position(
        "pos-tact-001",
        PositionKind.TACTICAL.value,
        "(tactical: mating net forced)",
        pv_branch_id="b-001-a",
        branches=(
            _b("b-001-a", "Qxh7+",
               info=0.95, forced=True,
               redundant=False, critical=True),
            _b("b-001-b", "Qe5",
               info=0.30, forced=False,
               redundant=False, critical=False),
            _b("b-001-c", "Bd3",
               info=0.20, forced=False,
               redundant=True,  critical=False),
            _b("b-001-d", "Nf3",
               info=0.15, forced=False,
               redundant=True,  critical=False),
            _b("b-001-e", "h3",
               info=0.10, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-tact-002",
        PositionKind.TACTICAL.value,
        "(tactical: bishop sac)",
        pv_branch_id="b-002-a",
        branches=(
            _b("b-002-a", "Bxh7+",
               info=0.92, forced=True,
               redundant=False, critical=True),
            _b("b-002-b", "Re1",
               info=0.25, forced=False,
               redundant=False, critical=False),
            _b("b-002-c", "Nbd2",
               info=0.18, forced=False,
               redundant=True,  critical=False),
            _b("b-002-d", "a3",
               info=0.08, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-quiet-001",
        PositionKind.QUIET.value,
        "(quiet: balanced development)",
        pv_branch_id="b-003-a",
        branches=(
            _b("b-003-a", "Nbd2",
               info=0.55, forced=False,
               redundant=False, critical=False),
            _b("b-003-b", "Nc3",
               info=0.52, forced=False,
               redundant=False, critical=False),
            _b("b-003-c", "h3",
               info=0.20, forced=False,
               redundant=True,  critical=False),
            _b("b-003-d", "a4",
               info=0.18, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-quiet-002",
        PositionKind.QUIET.value,
        "(quiet: slow maneuver)",
        pv_branch_id="b-004-a",
        branches=(
            _b("b-004-a", "Rfe1",
               info=0.50, forced=False,
               redundant=False, critical=False),
            _b("b-004-b", "Bd3",
               info=0.48, forced=False,
               redundant=False, critical=False),
            _b("b-004-c", "Bd2",
               info=0.45, forced=False,
               redundant=False, critical=False),
            _b("b-004-d", "Qc2",
               info=0.40, forced=False,
               redundant=False, critical=False),
            _b("b-004-e", "h3",
               info=0.15, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-middle-001",
        PositionKind.MIDDLEGAME.value,
        "(middlegame: pawn break)",
        pv_branch_id="b-005-a",
        branches=(
            _b("b-005-a", "e5",
               info=0.70, forced=False,
               redundant=False, critical=False),
            _b("b-005-b", "Nh4",
               info=0.55, forced=False,
               redundant=False, critical=False),
            _b("b-005-c", "Re1",
               info=0.40, forced=False,
               redundant=False, critical=False),
            _b("b-005-d", "Kh1",
               info=0.15, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-middle-002",
        PositionKind.MIDDLEGAME.value,
        "(middlegame: attack with sac threat)",
        pv_branch_id="b-006-a",
        branches=(
            _b("b-006-a", "Nxg7",
               info=0.88, forced=True,
               redundant=False, critical=True),
            _b("b-006-b", "Bxh6",
               info=0.40, forced=False,
               redundant=False, critical=False),
            _b("b-006-c", "Re3",
               info=0.30, forced=False,
               redundant=False, critical=False),
            _b("b-006-d", "Kh1",
               info=0.12, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-end-001",
        PositionKind.ENDGAME.value,
        "(endgame: forced winning king walk)",
        pv_branch_id="b-007-a",
        branches=(
            _b("b-007-a", "Kd5",
               info=0.95, forced=True,
               redundant=False, critical=False),
            _b("b-007-b", "Kd4",
               info=0.30, forced=False,
               redundant=True,  critical=False),
            _b("b-007-c", "Kc4",
               info=0.20, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-end-002",
        PositionKind.ENDGAME.value,
        "(endgame: pawn race)",
        pv_branch_id="b-008-a",
        branches=(
            _b("b-008-a", "a4",
               info=0.85, forced=True,
               redundant=False, critical=False),
            _b("b-008-b", "Kf3",
               info=0.50, forced=False,
               redundant=False, critical=False),
            _b("b-008-c", "Kg3",
               info=0.25, forced=False,
               redundant=True,  critical=False),
            _b("b-008-d", "Kh3",
               info=0.15, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-strat-001",
        PositionKind.STRATEGIC.value,
        "(strategic: outpost squeeze)",
        pv_branch_id="b-009-a",
        branches=(
            _b("b-009-a", "Nd5",
               info=0.70, forced=False,
               redundant=False, critical=False),
            _b("b-009-b", "Bb2",
               info=0.55, forced=False,
               redundant=False, critical=False),
            _b("b-009-c", "Qd2",
               info=0.45, forced=False,
               redundant=False, critical=False),
            _b("b-009-d", "Rfe1",
               info=0.30, forced=False,
               redundant=False, critical=False),
            _b("b-009-e", "h3",
               info=0.12, forced=False,
               redundant=True,  critical=False),
        ),
    ),
    Position(
        "pos-strat-002",
        PositionKind.STRATEGIC.value,
        "(strategic: minority attack)",
        pv_branch_id="b-010-a",
        branches=(
            _b("b-010-a", "b4",
               info=0.72, forced=False,
               redundant=False, critical=False),
            _b("b-010-b", "Rfb1",
               info=0.55, forced=False,
               redundant=False, critical=False),
            _b("b-010-c", "Qb3",
               info=0.40, forced=False,
               redundant=False, critical=False),
            _b("b-010-d", "Kh1",
               info=0.10, forced=False,
               redundant=True,  critical=False),
            _b("b-010-e", "a3",
               info=0.08, forced=False,
               redundant=True,  critical=False),
        ),
    ),
)


def fixture() -> tuple[Position, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        p.kind for p in fixture()
    ))


def total_branch_count() -> int:
    return sum(
        len(p.branches) for p in fixture()
    )


__all__ = [
    "Branch",
    "POSITION_KINDS",
    "Position",
    "PositionKind",
    "fixture",
    "kind_counts",
    "total_branch_count",
]
