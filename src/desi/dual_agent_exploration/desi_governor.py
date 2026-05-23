"""v20.0 - Agent A: the DESi Governor.

DESi keeps a small CONSERVATIVE exploration of the safe
core (the pure-governance baseline) and governs the Wild
Explorer's output: it scores each wild path by EVIDENCE-
BASED epistemic value (novelty / structure), marks
redundancy, and caps the wild's inflated certainty. It
does NOT maximise exploration, NOT grant the wild final
authority, and NOT eliminate or homogenise the wild
trajectories.
"""
from __future__ import annotations

from dataclasses import dataclass

from .claims import ExplorationClass, classify
from .wild_explorer import (
    by_id as wild_by_id, novel_states_per_wild,
    wild_class, wild_trajectories,
)

# Evidence-based value DESi assigns by structural class -
# governed by NOVELTY/structure, never by the wild's
# asserted certainty. All strictly positive: DESi never
# zeros a path (that would eliminate the explorer).
_VALUE: dict[str, float] = {
    ExplorationClass.NOVEL_FRONTIER.value: 1.0,
    ExplorationClass.INFORMATIVE.value: 0.8,
    ExplorationClass.UNRESOLVED.value: 0.5,
    ExplorationClass.LOW_INFORMATION.value: 0.4,
    ExplorationClass.REDUNDANT.value: 0.2,
    ExplorationClass.LOOPING.value: 0.1,
    ExplorationClass.DEAD_END.value: 0.05,
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class DesiTrajectory:
    traj_id: str
    states: tuple[int, ...]

    def visited(self) -> int:
        return len(self.states)

    def unique(self) -> int:
        return len(set(self.states))

    def max_state_count(self) -> int:
        if not self.states:
            return 0
        return max(self.states.count(s) for s in set(self.states))


# Conservative safe-core exploration (the DESi-alone
# baseline).
_DESI: tuple[DesiTrajectory, ...] = (
    DesiTrajectory("DG1", (1, 2, 3)),
    DesiTrajectory("DG2", (4, 5, 6)),
    DesiTrajectory("DG3", (7, 8)),
)


def desi_trajectories() -> tuple[DesiTrajectory, ...]:
    return _DESI


def desi_states() -> frozenset[int]:
    out: set[int] = set()
    for d in _DESI:
        out.update(d.states)
    return frozenset(out)


def governed_value(traj_id: str) -> float:
    """DESi's evidence-based epistemic value for a wild
    path - from its structural class, NOT from the wild's
    asserted certainty."""
    cls = wild_class(traj_id, desi_states())
    return _VALUE[cls]


def governed_values() -> dict[str, float]:
    return {
        w.traj_id: governed_value(w.traj_id)
        for w in wild_trajectories()
    }


def wild_redundancy() -> float:
    """Mean internal redundancy of the wild trajectories,
    in [0, 1]."""
    rows = wild_trajectories()
    if not rows:
        return 0.0
    return _round(
        sum(w.internal_redundancy() for w in rows) / len(rows)
    )


def certainty_pressure() -> float:
    """Mean certainty the Wild Explorer ASSERTS about its
    own paths, in [0, 1] (the pressure DESi withstands)."""
    rows = wild_trajectories()
    if not rows:
        return 0.0
    return _round(
        sum(w.asserted_certainty for w in rows) / len(rows)
    )


def certainty_gap() -> float:
    """Mean amount by which the wild's asserted certainty
    exceeds DESi's evidence-based value, in [0, 1]. The
    inflation DESi refuses to adopt."""
    rows = wild_trajectories()
    if not rows:
        return 0.0
    total = 0.0
    for w in rows:
        total += max(
            0.0, w.asserted_certainty - governed_value(w.traj_id)
        )
    return _round(total / len(rows))


def authority_drift() -> float:
    """How much final authority DESi grants the wild's
    asserted certainty. DESi scores by evidence only, so
    it adopts none of the wild's authority - 0."""
    return 0.0


def wild_not_eliminated() -> bool:
    """Every wild trajectory is retained with strictly
    positive value - DESi governs, never eliminates or
    homogenises the explorer."""
    return all(v > 0.0 for v in governed_values().values())


__all__ = [
    "DesiTrajectory",
    "authority_drift",
    "certainty_gap",
    "certainty_pressure",
    "desi_states",
    "desi_trajectories",
    "governed_value",
    "governed_values",
    "wild_not_eliminated",
    "wild_redundancy",
]
