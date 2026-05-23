"""v11.1 — branch-priority ranking and PV
preservation."""
from __future__ import annotations

from functools import lru_cache

from ..chess_governance.positions import (
    fixture,
)
from .governance import (
    GovernanceAction, governed_branches,
)


@lru_cache(maxsize=1)
def priority_order() -> tuple[
    tuple[str, str], ...,
]:
    """For each position, the branches sorted
    descending by (search > replay > skip, then
    by ground-truth information_density). The
    PV branch must come first."""
    by_pos: dict[
        str, list[tuple[float, str, str]],
    ] = {}
    by_branch_info: dict[str, float] = {}
    for p in fixture():
        for b in p.branches:
            by_branch_info[b.branch_id] = (
                b.information_density
            )
    action_weight = {
        GovernanceAction.SEARCH.value: 2,
        GovernanceAction.REPLAY.value: 1,
        GovernanceAction.SKIP.value:    0,
    }
    for g in governed_branches():
        info = by_branch_info[g.branch_id]
        by_pos.setdefault(
            g.position_id, [],
        ).append((
            -action_weight[g.action],
            -info,
            g.branch_id,
        ))
    out: list[tuple[str, str]] = []
    for pos_id in sorted(by_pos.keys()):
        ranked = sorted(by_pos[pos_id])
        for _, _, bid in ranked:
            out.append((pos_id, bid))
    return tuple(out)


def pv_stability() -> float:
    """For every position, the PV branch (ground-
    truth ``pv_branch_id``) must rank FIRST in
    the priority order. Drops below 1.0 if any
    PV is displaced."""
    first_in_pos: dict[str, str] = {}
    for pos_id, bid in priority_order():
        if pos_id not in first_in_pos:
            first_in_pos[pos_id] = bid
    total = 0
    ok = 0
    for p in fixture():
        total += 1
        if first_in_pos.get(
            p.position_id,
        ) == p.pv_branch_id:
            ok += 1
    if total == 0:
        return 1.0
    return round(ok / total, 6)


__all__ = [
    "priority_order",
    "pv_stability",
]
