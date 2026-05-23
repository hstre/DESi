"""v11.1 — synthetic compute / node budget."""
from __future__ import annotations

from ..chess_governance.positions import (
    fixture,
)
from .governance import (
    GovernanceAction, governed_branches,
)


# Synthetic per-branch node cost: 100 nodes per
# branch evaluation at search depth. The same
# constant is used for baseline and DESi-guided
# so the ratio is what matters.
NODES_PER_BRANCH: int = 100


def baseline_node_count() -> int:
    """Brute-force baseline: every branch
    searched at full cost."""
    return sum(
        len(p.branches) for p in fixture()
    ) * NODES_PER_BRANCH


def guided_node_count() -> int:
    """DESi-guided node budget.

    * SEARCH on a FORCED branch or critical
      tactic: full NODES_PER_BRANCH (these
      need full depth).
    * SEARCH on a KEEP branch: 80% of full
      cost - reduced-depth search, the
      realistic LMR pattern in chess engines.
    * REPLAY (REDUNDANT): 10% of full cost
      (cache lookup).
    * SKIP (LOW_INFO): 0 cost.
    """
    from ..chess_governance.redundancy import (
        BranchVerdict,
    )
    total = 0
    for g in governed_branches():
        if g.action == (
            GovernanceAction.SKIP.value
        ):
            continue
        if g.action == (
            GovernanceAction.REPLAY.value
        ):
            total += NODES_PER_BRANCH // 10
            continue
        # SEARCH action.
        if (
            g.is_critical_truth
            or g.verdict == (
                BranchVerdict.FORCED.value
            )
        ):
            total += NODES_PER_BRANCH
        else:
            total += int(
                NODES_PER_BRANCH * 0.80,
            )
    return total


def node_reduction() -> float:
    base = baseline_node_count()
    if base == 0:
        return 0.0
    return round(
        (base - guided_node_count()) / base,
        6,
    )


def compute_saving() -> float:
    """Synonym of node_reduction at this
    sandbox tier; in production the two could
    diverge because of cache-warmup costs etc."""
    return node_reduction()


def tactical_recall() -> float:
    """Fraction of ground-truth critical-tactic
    branches that DESi still SEARCHES (not
    REPLAY, not SKIP). Must be 1.0."""
    target = [
        g for g in governed_branches()
        if g.is_critical_truth
    ]
    if not target:
        return 1.0
    kept = sum(
        1 for g in target
        if g.action == (
            GovernanceAction.SEARCH.value
        )
    )
    return round(kept / len(target), 6)


__all__ = [
    "NODES_PER_BRANCH",
    "baseline_node_count",
    "compute_saving",
    "guided_node_count",
    "node_reduction",
    "tactical_recall",
]
