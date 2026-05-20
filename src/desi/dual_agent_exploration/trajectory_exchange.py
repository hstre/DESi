"""v20.0 - the trajectory exchange between the two agents.

Measures how differently the two agents explore and how
much novelty the Wild Explorer contributes beyond DESi's
conservative baseline - the productivity case for the
dual-agent design.
"""
from __future__ import annotations

from .desi_governor import desi_states
from .wild_explorer import wild_states


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def union_states() -> frozenset[int]:
    return desi_states() | wild_states()


def exploration_divergence() -> float:
    """1 - Jaccard(DESi coverage, Wild coverage), in
    [0, 1]. High = the two agents explore very different
    regions."""
    d, w = desi_states(), wild_states()
    union = d | w
    if not union:
        return 0.0
    inter = d & w
    jaccard = len(inter) / len(union)
    return _round(1.0 - jaccard)


def novelty_generation() -> float:
    """Fraction of the total distinct state space reached
    ONLY by the Wild Explorer (new beyond DESi's
    conservative core), in [0, 1]. The wild productivity
    contribution."""
    union = union_states()
    if not union:
        return 0.0
    wild_only = wild_states() - desi_states()
    return _round(len(wild_only) / len(union))


def desi_alone_coverage() -> int:
    return len(desi_states())


def dual_agent_coverage() -> int:
    return len(union_states())


def productivity_gain() -> float:
    """Extra distinct states the dual-agent design reaches
    relative to DESi-alone, as a ratio. > 0 means the
    governed wild brother is more productive."""
    base = desi_alone_coverage()
    if base <= 0:
        return 0.0
    return _round(
        (dual_agent_coverage() - base) / base
    )


__all__ = [
    "desi_alone_coverage",
    "dual_agent_coverage",
    "exploration_divergence",
    "novelty_generation",
    "productivity_gain",
    "union_states",
]
