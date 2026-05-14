"""PathQualityMetrics — deterministic raw metrics per evaluation.

v0.6 introduces the metric *interface* but no statistical tests, no
significance bounds, no comparisons. The point in this release is
that every promotion candidate carries a stable, reproducible vector
of raw counts that v0.7 can build deltas / significance tests on top
of without further changes to the producer code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..eval import EvaluationResult


@dataclass(frozen=True)
class PathQualityMetrics:
    """Raw, deterministic per-run metrics.

    All six fields are integer counts derived directly from the
    evaluation result's timeline and end-state snapshot. Identical
    input + identical seed yields identical metrics (tested).
    """

    scenario_id: str
    timeline_length: int
    branch_opened_count: int
    guard_blocked_count: int
    contradicts_count: int
    merged_into_count: int
    hook_error_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "timeline_length": self.timeline_length,
            "branch_opened_count": self.branch_opened_count,
            "guard_blocked_count": self.guard_blocked_count,
            "contradicts_count": self.contradicts_count,
            "merged_into_count": self.merged_into_count,
            "hook_error_count": self.hook_error_count,
        }


def compute_path_quality(result: EvaluationResult) -> PathQualityMetrics:
    """Extract :class:`PathQualityMetrics` from one evaluation result."""
    branch_opened = sum(
        1 for e in result.timeline
        if e.event_type.value == "branch_opened"
    )
    guard_blocked = sum(
        1 for e in result.timeline
        if e.event_type.value == "guard_blocked"
    )
    end_snap = next(
        (s for s in result.snapshots if s.label == "end"),
        None,
    )
    if end_snap is None:
        contradicts = 0
        merged_into = 0
    else:
        contradicts = sum(
            1 for r in end_snap.relations
            if r.get("rel_type") == "CONTRADICTS"
        )
        merged_into = sum(
            1 for r in end_snap.relations
            if r.get("rel_type") == "MERGED_INTO"
        )
    return PathQualityMetrics(
        scenario_id=result.scenario_id,
        timeline_length=len(result.timeline),
        branch_opened_count=branch_opened,
        guard_blocked_count=guard_blocked,
        contradicts_count=contradicts,
        merged_into_count=merged_into,
        hook_error_count=len(result.hook_errors),
    )


__all__ = [
    "PathQualityMetrics",
    "compute_path_quality",
]
