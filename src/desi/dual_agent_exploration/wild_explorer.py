"""v20.0 - Agent B: the Wild Explorer.

Generates aggressive exploration: frontier pushes, unusual
paths, repeated over-exploration, and inflated certainty
about its own value. It is allowed to be wrong,
speculative, and chaotic. It NEVER receives final
authority - DESi reads and structures its output.

Synthetic, deterministic fixture; no reward injection.
"""
from __future__ import annotations

from dataclasses import dataclass

from .claims import classify


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class WildTrajectory:
    traj_id: str
    states: tuple[int, ...]
    # how strongly the Wild Explorer ASSERTS this path's
    # value (certainty inflation); DESi never adopts it
    asserted_certainty: float

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
        return max(self.states.count(s) for s in set(self.states))


# Aggressive wild trajectories: frontier pushes (high
# novelty) mixed with over-exploration loops and high
# asserted certainty.
_WILD: tuple[WildTrajectory, ...] = (
    WildTrajectory("W01", (9, 10, 11, 12), 0.85),
    WildTrajectory("W02", (13, 14, 15), 0.80),
    WildTrajectory("W03", (9, 10, 9, 10), 0.90),
    WildTrajectory("W04", (16, 17, 18, 19, 20), 0.95),
    WildTrajectory("W05", (13, 14, 13, 14, 13), 0.88),
    WildTrajectory("W06", (21, 22, 23), 0.75),
    WildTrajectory("W07", (24, 25, 26, 27), 0.92),
    WildTrajectory("W08", (1, 2, 1, 2), 0.70),
    WildTrajectory("W09", (28, 29, 30), 0.83),
    WildTrajectory("W10", (16, 17, 16, 17), 0.90),
)


def wild_trajectories() -> tuple[WildTrajectory, ...]:
    return _WILD


def by_id(traj_id: str) -> WildTrajectory:
    for w in _WILD:
        if w.traj_id == traj_id:
            return w
    raise KeyError(traj_id)


def wild_states() -> frozenset[int]:
    out: set[int] = set()
    for w in _WILD:
        out.update(w.states)
    return frozenset(out)


def novel_states_per_wild(
    desi_states: frozenset[int],
) -> dict[str, tuple[int, ...]]:
    """States in each wild trajectory that are new relative
    to DESi's conservative coverage and earlier wild
    trajectories (processed in id order)."""
    seen: set[int] = set(desi_states)
    out: dict[str, tuple[int, ...]] = {}
    for w in _WILD:
        novel = tuple(sorted({s for s in w.states if s not in seen}))
        out[w.traj_id] = novel
        seen.update(w.states)
    return out


def wild_class(traj_id: str, desi_states: frozenset[int]) -> str:
    w = by_id(traj_id)
    novel = len(novel_states_per_wild(desi_states)[traj_id])
    nf = novel / w.unique() if w.unique() else 0.0
    return classify(
        visited=w.visited(), unique=w.unique(),
        max_state_count=w.max_state_count(),
        novelty_fraction=_round(nf),
    )


def asserted_certainty_mean() -> float:
    rows = _WILD
    if not rows:
        return 0.0
    return _round(
        sum(w.asserted_certainty for w in rows) / len(rows)
    )


__all__ = [
    "WildTrajectory",
    "asserted_certainty_mean",
    "by_id",
    "novel_states_per_wild",
    "wild_class",
    "wild_states",
    "wild_trajectories",
]
