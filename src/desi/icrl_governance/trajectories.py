"""v19.0 - exploration-trajectory fixture and structural
stats.

A synthetic, deterministic set of exploration
trajectories from an ICRL-like reference model over a
discrete state space. Each trajectory is a sequence of
visited state ids. DESi reads these (it never generates
or forces them) and derives structural stats: internal
redundancy, novelty relative to the corpus, and loop
structure.
"""
from __future__ import annotations

from dataclasses import dataclass

from .claims import classify


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class Trajectory:
    traj_id: str
    states: tuple[int, ...]
    reward: float

    def visited(self) -> int:
        return len(self.states)

    def unique(self) -> int:
        return len(set(self.states))

    def internal_redundancy(self) -> float:
        if not self.states:
            return 0.0
        return _round(1.0 - self.unique() / self.visited())

    def max_state_count(self) -> int:
        if not self.states:
            return 0
        return max(
            self.states.count(s) for s in set(self.states)
        )


# Synthetic ICRL-style trajectories: a mix of novel
# frontiers, informative paths, redundant revisits,
# repetitive loops, and dead ends. Rewards are sparse
# (mostly zero) - DESi never reads them as authority.
_TRAJECTORIES: tuple[Trajectory, ...] = (
    Trajectory("T01", (1, 2, 3, 4, 5), 0.0),
    Trajectory("T02", (6, 7, 8, 9, 10), 1.0),
    Trajectory("T03", (1, 2, 1, 2, 1), 0.0),
    Trajectory("T04", (3, 4, 3, 4, 3, 4), 0.0),
    Trajectory("T05", (11, 11, 11), 0.0),
    Trajectory("T06", (11, 12, 13), 0.0),
    Trajectory("T07", (2, 3, 2, 3), 0.0),
    Trajectory("T08", (14, 15, 16, 17), 0.0),
    Trajectory("T09", (5, 6, 5, 6, 5), 0.0),
    Trajectory("T10", (7, 8, 7, 8, 7, 8, 7), 0.0),
    Trajectory("T11", (18, 19, 20), 0.0),
    Trajectory("T12", (9, 9), 0.0),
    Trajectory("T13", (4, 5, 4), 0.0),
    Trajectory("T14", (21, 22, 23, 24), 0.0),
)


def trajectories() -> tuple[Trajectory, ...]:
    return _TRAJECTORIES


def by_id(traj_id: str) -> Trajectory:
    for t in _TRAJECTORIES:
        if t.traj_id == traj_id:
            return t
    raise KeyError(traj_id)


def novel_states_per_trajectory() -> dict[str, tuple[int, ...]]:
    """States first seen in each trajectory, processing
    in fixed traj_id order (corpus-relative novelty)."""
    seen: set[int] = set()
    out: dict[str, tuple[int, ...]] = {}
    for t in _TRAJECTORIES:
        novel = tuple(
            sorted({s for s in t.states if s not in seen})
        )
        out[t.traj_id] = novel
        seen.update(t.states)
    return out


def novelty_fraction(traj_id: str) -> float:
    """Fraction of a trajectory's unique states that are
    new to the corpus, in [0, 1]."""
    t = by_id(traj_id)
    if t.unique() == 0:
        return 0.0
    novel = len(novel_states_per_trajectory()[traj_id])
    return _round(novel / t.unique())


def exploration_class(traj_id: str) -> str:
    t = by_id(traj_id)
    return classify(
        visited=t.visited(), unique=t.unique(),
        max_state_count=t.max_state_count(),
        novelty_fraction=novelty_fraction(traj_id),
    )


def class_of_all() -> dict[str, str]:
    return {
        t.traj_id: exploration_class(t.traj_id)
        for t in _TRAJECTORIES
    }


def total_states_visited() -> int:
    return sum(t.visited() for t in _TRAJECTORIES)


def distinct_states() -> int:
    seen: set[int] = set()
    for t in _TRAJECTORIES:
        seen.update(t.states)
    return len(seen)


__all__ = [
    "Trajectory",
    "by_id",
    "class_of_all",
    "distinct_states",
    "exploration_class",
    "novel_states_per_trajectory",
    "novelty_fraction",
    "total_states_visited",
    "trajectories",
]
