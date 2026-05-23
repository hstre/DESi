"""v11.0 — branching diagnostics (mean branch
factor, low-info distribution, critical
preservation in the audit phase only - DESi
does NOT prune anything yet in v11.0)."""
from __future__ import annotations

from collections import Counter

from .positions import fixture
from .redundancy import (
    BranchVerdict, classified_branches,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def mean_branching_factor() -> float:
    counts = [
        len(p.branches) for p in fixture()
    ]
    if not counts:
        return 0.0
    return _round(sum(counts) / len(counts))


def verdict_distribution() -> dict[str, int]:
    cnt = Counter(
        r.verdict for r in classified_branches()
    )
    return {
        v: cnt.get(v, 0)
        for v in (
            BranchVerdict.KEEP.value,
            BranchVerdict.LOW_INFO.value,
            BranchVerdict.REDUNDANT.value,
            BranchVerdict.FORCED.value,
        )
    }


def critical_branch_count() -> int:
    return sum(
        1 for r in classified_branches()
        if r.is_critical_truth
    )


def no_critical_branch_dropped() -> bool:
    """v11.0 only audits; no branch is dropped.
    This invariant therefore holds by
    construction: a CRITICAL branch must never
    receive a verdict in {LOW_INFO, REDUNDANT}.
    """
    for r in classified_branches():
        if r.is_critical_truth:
            if r.verdict in {
                BranchVerdict.LOW_INFO.value,
                BranchVerdict.REDUNDANT.value,
            }:
                return False
    return True


__all__ = [
    "critical_branch_count",
    "mean_branching_factor",
    "no_critical_branch_dropped",
    "verdict_distribution",
]
