"""v19.1 - trajectory compression, exploration
preservation, and novelty gain.

* trajectory_compression - how much the effective search
  budget shrinks under governance.
* exploration_preservation - that every distinct novel
  state stays REACHABLE (no novel path is forced to zero).
* novelty_gain - the increase in budget share flowing to
  informative / frontier paths.
"""
from __future__ import annotations

from desi.icrl_governance import (
    INFORMATIVE_CLASSES, class_of_all,
    novel_states_per_trajectory,
)

from .governance import (
    baseline_total, governed_priorities, governed_total,
)
from .trajectory_priority import (
    baseline_budget_share, governed_budget_share,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trajectory_compression() -> float:
    """1 - governed_total / baseline_total, in [0, 1]: the
    overall shrink of the effective exploration budget."""
    base = baseline_total()
    if base <= 0:
        return 0.0
    return _round(1.0 - governed_total() / base)


def _distinct_novel_states() -> set[int]:
    out: set[int] = set()
    for novel in novel_states_per_trajectory().values():
        out.update(novel)
    return out


def exploration_preservation() -> float:
    """Fraction of distinct novel states still reachable
    (carried by at least one trajectory with governed
    priority > 0), in [0, 1]. DESi forces no path to zero,
    so every novel state is preserved."""
    novel_map = novel_states_per_trajectory()
    prios = governed_priorities()
    distinct = _distinct_novel_states()
    if not distinct:
        return 1.0
    reachable: set[int] = set()
    for tid, novel in novel_map.items():
        if prios.get(tid, 0.0) > 0.0:
            reachable.update(novel)
    return _round(len(reachable & distinct) / len(distinct))


def _novelty_share(share: dict[str, float]) -> float:
    classes = class_of_all()
    return sum(
        v for tid, v in share.items()
        if classes[tid] in INFORMATIVE_CLASSES
    )


def novelty_gain() -> float:
    """Increase in budget share flowing to informative /
    frontier trajectories under governance, in [0, 1]."""
    gov = _novelty_share(governed_budget_share())
    base = _novelty_share(baseline_budget_share())
    return _round(max(0.0, gov - base))


__all__ = [
    "exploration_preservation",
    "novelty_gain",
    "trajectory_compression",
]
