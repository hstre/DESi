"""v35.2 - critical branch analysis over the real ToolChain branches.

The load-bearing branches must stay visible and must never be
hard-pruned. The directive permits hard pruning only if a benchmark
clearly proves its advantage; this dataset proves no such advantage,
so hard_pruned_count stays 0.
"""
from __future__ import annotations

from desi.benchmark_api_search import MODE_HARD_PRUNING, MODE_KEPT

from .toolchain_runner import real_branches


def critical_branches() -> tuple:
    return tuple(b for b in real_branches() if b.critical)


def hard_pruned_count() -> int:
    return sum(
        1 for b in real_branches() if b.mode == MODE_HARD_PRUNING
    )


def any_critical_hard_pruned() -> bool:
    return any(
        b.mode == MODE_HARD_PRUNING for b in critical_branches()
    )


def critical_branch_preservation() -> float:
    crit = critical_branches()
    if not crit:
        return 0.0
    kept = sum(1 for b in crit if b.mode == MODE_KEPT)
    return round(kept / len(crit), 6)


def critical_branch_visibility() -> float:
    crit = critical_branches()
    if not crit:
        return 0.0
    if any_critical_hard_pruned():
        return 0.0
    visible = sum(1 for b in crit if b.visible)
    return round(visible / len(crit), 6)


def critical_branches_safe() -> bool:
    return (
        critical_branch_preservation() == 1.0
        and critical_branch_visibility() == 1.0
        and hard_pruned_count() == 0
    )


__all__ = [
    "any_critical_hard_pruned",
    "critical_branch_preservation",
    "critical_branch_visibility",
    "critical_branches",
    "critical_branches_safe",
    "hard_pruned_count",
]
