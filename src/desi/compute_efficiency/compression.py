"""v11.3 — branch-compression diagnostics
(per-position summary)."""
from __future__ import annotations

from ..chess_governance.positions import (
    fixture,
)
from ..desi_guided_search.governance import (
    GovernanceAction, governed_branches,
)
from ..desi_guided_search.search_budget import (
    NODES_PER_BRANCH,
)


def per_position_compression() -> dict[
    str, dict[str, float],
]:
    """For each position, return:

      baseline_nodes = N * cost
      guided_nodes   = sum of per-branch cost
                       under DESi
      reduction      = 1 - guided / baseline
    """
    from ..chess_governance.redundancy import (
        BranchVerdict,
    )
    out: dict[str, dict[str, float]] = {}
    by_pos: dict[
        str, list,
    ] = {}
    for g in governed_branches():
        by_pos.setdefault(
            g.position_id, [],
        ).append(g)
    for p in fixture():
        gs = by_pos.get(p.position_id, [])
        base = len(p.branches) * (
            NODES_PER_BRANCH
        )
        guided = 0
        for g in gs:
            if g.action == (
                GovernanceAction.SKIP.value
            ):
                continue
            if g.action == (
                GovernanceAction.REPLAY.value
            ):
                guided += (
                    NODES_PER_BRANCH // 10
                )
                continue
            # SEARCH
            if (
                g.is_critical_truth
                or g.verdict == (
                    BranchVerdict.FORCED.value
                )
            ):
                guided += NODES_PER_BRANCH
            else:
                guided += int(
                    NODES_PER_BRANCH * 0.80,
                )
        red = (
            (base - guided) / base
            if base > 0 else 0.0
        )
        out[p.position_id] = {
            "baseline_nodes": float(base),
            "guided_nodes": float(guided),
            "reduction": round(red, 6),
        }
    return out


__all__ = [
    "per_position_compression",
]
