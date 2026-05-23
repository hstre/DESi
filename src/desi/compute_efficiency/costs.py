"""v11.3 — synthetic cost model.

Three cost dimensions:

* ``nodes`` - already pulled from v11.1.
* ``time_ms`` - 1 ms per node (a constant
  scaling).
* ``energy_proxy`` - cost-per-node scaled by a
  per-action multiplier (SEARCH at full depth
  is more energy-intensive than REPLAY).
"""
from __future__ import annotations

from ..desi_guided_search.search_budget import (
    baseline_node_count, guided_node_count,
)


_TIME_PER_NODE_MS: float = 1.0


# Energy multipliers per action: full SEARCH
# costs more energy per node than REPLAY (cache
# lookups are cheap).
_ENERGY_MULTIPLIER_SEARCH: float = 1.0
_ENERGY_MULTIPLIER_REPLAY: float = 0.30
_ENERGY_MULTIPLIER_SKIP:   float = 0.0


def baseline_time_ms() -> float:
    return round(
        baseline_node_count()
        * _TIME_PER_NODE_MS, 6,
    )


def guided_time_ms() -> float:
    return round(
        guided_node_count()
        * _TIME_PER_NODE_MS, 6,
    )


def baseline_energy() -> float:
    """Baseline searches every branch at full
    SEARCH energy."""
    return round(
        baseline_node_count()
        * _ENERGY_MULTIPLIER_SEARCH, 6,
    )


def guided_energy() -> float:
    """Guided energy accounts for action
    multipliers: SKIP is zero, REPLAY is 0.3x,
    SEARCH is 1x."""
    from ..desi_guided_search.governance import (
        GovernanceAction, governed_branches,
    )
    from ..desi_guided_search.search_budget import (
        NODES_PER_BRANCH,
    )
    from ..chess_governance.redundancy import (
        BranchVerdict,
    )
    energy = 0.0
    for g in governed_branches():
        if g.action == (
            GovernanceAction.SKIP.value
        ):
            mult = _ENERGY_MULTIPLIER_SKIP
            cost = 0.0
        elif g.action == (
            GovernanceAction.REPLAY.value
        ):
            mult = _ENERGY_MULTIPLIER_REPLAY
            cost = NODES_PER_BRANCH // 10
        else:
            mult = _ENERGY_MULTIPLIER_SEARCH
            if (
                g.is_critical_truth
                or g.verdict == (
                    BranchVerdict.FORCED.value
                )
            ):
                cost = NODES_PER_BRANCH
            else:
                cost = int(
                    NODES_PER_BRANCH * 0.80,
                )
        energy += cost * mult
    return round(energy, 6)


__all__ = [
    "baseline_energy",
    "baseline_time_ms",
    "guided_energy",
    "guided_time_ms",
]
