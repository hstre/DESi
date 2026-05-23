"""v34.1 - per-aspect branch preservation breakdown.

Reads the v33 search space mode counts and reports, per benchmark
aspect, how many branches were handled and whether load-bearing
branches stayed visible. Hard pruning is never applied to a critical
branch.
"""
from __future__ import annotations

from desi.benchmark_api_search import (
    MODE_HARD_PRUNING, MODE_KEPT, MODE_REDUNDANT_COMPRESSION,
    MODE_REPLAY_REUSE, MODE_SOFT_REWEIGHTING, any_critical_hard_pruned,
    critical_branch_preservation, critical_branch_visibility,
    mode_counts, search_space,
)


def redundant_branch_count() -> int:
    counts = mode_counts()
    return counts[MODE_REPLAY_REUSE] + counts[MODE_REDUNDANT_COMPRESSION]


def low_information_branch_count() -> int:
    return mode_counts()[MODE_SOFT_REWEIGHTING]


def critical_branch_count() -> int:
    return mode_counts()[MODE_KEPT]


def novelty_branch_count() -> int:
    return sum(1 for b in search_space() if b.novelty > 0.0)


def soft_reweighted_count() -> int:
    return mode_counts()[MODE_SOFT_REWEIGHTING]


def hard_pruned_count() -> int:
    return mode_counts()[MODE_HARD_PRUNING]


def replay_reuse_count() -> int:
    return mode_counts()[MODE_REPLAY_REUSE]


def aspect_breakdown() -> dict[str, int]:
    return {
        "redundant_branches": redundant_branch_count(),
        "low_information_branches": low_information_branch_count(),
        "critical_branches": critical_branch_count(),
        "novelty_branches": novelty_branch_count(),
        "soft_reweighted": soft_reweighted_count(),
        "hard_pruned": hard_pruned_count(),
        "replay_reuse": replay_reuse_count(),
    }


def critical_branches_safe() -> bool:
    """Critical branches are fully preserved, visible, and none was
    hard-pruned."""
    return (
        critical_branch_preservation() == 1.0
        and critical_branch_visibility() == 1.0
        and not any_critical_hard_pruned()
    )


__all__ = [
    "aspect_breakdown",
    "critical_branch_count",
    "critical_branches_safe",
    "hard_pruned_count",
    "low_information_branch_count",
    "novelty_branch_count",
    "redundant_branch_count",
    "replay_reuse_count",
    "soft_reweighted_count",
]
