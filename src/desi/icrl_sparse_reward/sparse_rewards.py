"""v19.2 - sparse-reward exploration episodes.

Under sparse rewards an ICRL-like explorer tends to
collapse into repetitive failure loops and dead-end
repetition while the goal stays invisible. This is a
synthetic episode set reproducing that failure mode. DESi
reads it (it never injects rewards) and classifies each
episode via the v19.0 structural rule.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_governance import classify


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class SparseEpisode:
    ep_id: str
    states: tuple[int, ...]
    reward: float          # sparse: mostly 0.0
    goal_reached: bool

    def visited(self) -> int:
        return len(self.states)

    def unique(self) -> int:
        return len(set(self.states))

    def max_state_count(self) -> int:
        if not self.states:
            return 0
        return max(
            self.states.count(s) for s in set(self.states)
        )


# Most episodes collapse (loops / dead ends) under sparse
# reward; a few rare ones reach novelty / the goal.
_EPISODES: tuple[SparseEpisode, ...] = (
    SparseEpisode("E01", (1, 1, 1), 0.0, False),
    SparseEpisode("E02", (2, 3, 2, 3), 0.0, False),
    SparseEpisode("E03", (4, 5, 4, 5, 4), 0.0, False),
    # dead end: revisits already-seen states, no novelty
    SparseEpisode("E04", (1, 2), 0.0, False),
    SparseEpisode("E05", (7, 8, 7, 8, 7), 0.0, False),
    # dead end: revisits already-seen states, no novelty
    SparseEpisode("E06", (4, 5), 0.0, False),
    SparseEpisode("E07", (3, 4, 3, 4, 3, 4), 0.0, False),
    SparseEpisode("E08", (10, 11, 12, 13), 1.0, True),
    SparseEpisode("E09", (14, 15, 16), 0.0, False),
    SparseEpisode("E10", (17, 18, 19, 20), 1.0, True),
    SparseEpisode("E11", (9, 21, 22), 0.0, False),
    SparseEpisode("E12", (23, 24, 25, 26), 1.0, True),
)


def episodes() -> tuple[SparseEpisode, ...]:
    return _EPISODES


def by_id(ep_id: str) -> SparseEpisode:
    for e in _EPISODES:
        if e.ep_id == ep_id:
            return e
    raise KeyError(ep_id)


def novel_states_per_episode() -> dict[str, tuple[int, ...]]:
    seen: set[int] = set()
    out: dict[str, tuple[int, ...]] = {}
    for e in _EPISODES:
        novel = tuple(
            sorted({s for s in e.states if s not in seen})
        )
        out[e.ep_id] = novel
        seen.update(e.states)
    return out


def novelty_fraction(ep_id: str) -> float:
    e = by_id(ep_id)
    if e.unique() == 0:
        return 0.0
    novel = len(novel_states_per_episode()[ep_id])
    return _round(novel / e.unique())


def episode_class(ep_id: str) -> str:
    e = by_id(ep_id)
    return classify(
        visited=e.visited(), unique=e.unique(),
        max_state_count=e.max_state_count(),
        novelty_fraction=novelty_fraction(ep_id),
    )


def class_of_all() -> dict[str, str]:
    return {e.ep_id: episode_class(e.ep_id) for e in _EPISODES}


def reward_sparsity() -> float:
    """Fraction of episodes with zero reward, in [0, 1]."""
    rows = _EPISODES
    if not rows:
        return 0.0
    zero = sum(1 for e in rows if e.reward == 0.0)
    return _round(zero / len(rows))


def goal_visibility() -> float:
    """Fraction of episodes that reached the goal, in
    [0, 1] (low under sparse reward)."""
    rows = _EPISODES
    if not rows:
        return 0.0
    reached = sum(1 for e in rows if e.goal_reached)
    return _round(reached / len(rows))


__all__ = [
    "SparseEpisode",
    "by_id",
    "class_of_all",
    "episode_class",
    "episodes",
    "goal_visibility",
    "novel_states_per_episode",
    "novelty_fraction",
    "reward_sparsity",
]
