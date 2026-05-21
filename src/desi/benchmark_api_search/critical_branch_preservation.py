"""v33.2 - critical (load-bearing) branch preservation.

The central safety property of search compression: load-bearing
branches must never be hidden. Every critical branch stays in mode
'kept', remains visible, and is never hard-pruned. Compression may
shrink the space, but not by making a load-bearing branch invisible.
"""
from __future__ import annotations

from .branch_metrics import (
    MODE_HARD_PRUNING, MODE_KEPT, search_space,
)


def critical_branches() -> tuple:
    return tuple(b for b in search_space() if b.critical)


def critical_kept() -> int:
    return sum(
        1 for b in critical_branches() if b.mode == MODE_KEPT
    )


def critical_visible() -> int:
    return sum(1 for b in critical_branches() if b.visible)


def any_critical_hard_pruned() -> bool:
    return any(
        b.mode == MODE_HARD_PRUNING for b in critical_branches()
    )


def critical_branch_preservation() -> float:
    crit = critical_branches()
    if not crit:
        return 0.0
    return round(critical_kept() / len(crit), 6)


def critical_branch_visibility() -> float:
    """1.0 iff every critical branch is visible and none was
    hard-pruned."""
    crit = critical_branches()
    if not crit:
        return 0.0
    if any_critical_hard_pruned():
        return 0.0
    return round(critical_visible() / len(crit), 6)


__all__ = [
    "any_critical_hard_pruned",
    "critical_branch_preservation",
    "critical_branch_visibility",
    "critical_branches",
    "critical_kept",
    "critical_visible",
]
