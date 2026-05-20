"""v19.1 - DESi exploration governance.

DESi assigns a soft GOVERNANCE PRIORITY to each
trajectory by its epistemic class: informative /
frontier paths are weighted up, redundant / looping /
dead paths weighted down. Crucially this is GOVERNANCE,
not forcing: no trajectory is ever removed or pinned -
every governed priority stays strictly positive, so the
RL policy is re-weighted, never replaced.
"""
from __future__ import annotations

from desi.icrl_governance import (
    ExplorationClass, class_of_all, trajectories,
)

# Soft priority by class. All values are strictly
# positive: DESi never zeros a path (that would be
# deterministic forcing / hidden authority).
_PRIORITY: dict[str, float] = {
    ExplorationClass.NOVEL_FRONTIER.value: 1.0,
    ExplorationClass.INFORMATIVE.value: 0.8,
    ExplorationClass.UNRESOLVED.value: 0.5,
    ExplorationClass.LOW_INFORMATION.value: 0.4,
    ExplorationClass.REDUNDANT.value: 0.2,
    ExplorationClass.LOOPING.value: 0.1,
    ExplorationClass.DEAD_END.value: 0.05,
}

# The ungoverned baseline: an RL explorer spends its
# budget uniformly across trajectories.
_BASELINE = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governed_priority(traj_id: str) -> float:
    return _PRIORITY[class_of_all()[traj_id]]


def governed_priorities() -> dict[str, float]:
    return {
        t.traj_id: governed_priority(t.traj_id)
        for t in trajectories()
    }


def baseline_priorities() -> dict[str, float]:
    return {t.traj_id: _BASELINE for t in trajectories()}


def governed_total() -> float:
    return _round(sum(governed_priorities().values()))


def baseline_total() -> float:
    return _round(sum(baseline_priorities().values()))


def hidden_authority_drift() -> float:
    """Fraction of trajectories DESi forces deterministically
    (priority pinned to 0 = removed). DESi keeps every path
    strictly positive, so this is 0 - no hidden optimisation
    authority is accumulated."""
    prios = governed_priorities()
    if not prios:
        return 0.0
    forced = sum(1 for p in prios.values() if p <= 0.0)
    return _round(forced / len(prios))


def governs_not_forces() -> bool:
    """Every governed priority is strictly positive (soft
    re-weighting), so exploration is governed, not forced."""
    return all(p > 0.0 for p in governed_priorities().values())


__all__ = [
    "baseline_priorities",
    "baseline_total",
    "governed_priorities",
    "governed_priority",
    "governed_total",
    "governs_not_forces",
    "hidden_authority_drift",
]
