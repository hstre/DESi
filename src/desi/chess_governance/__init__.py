"""DESi v11.0 - chess search redundancy audit
(read-only, no live engine)."""
from __future__ import annotations

from .branching import (
    critical_branch_count,
    mean_branching_factor,
    no_critical_branch_dropped,
    verdict_distribution,
)
from .positions import (
    Branch, POSITION_KINDS, Position,
    PositionKind, fixture, kind_counts,
    total_branch_count,
)
from .redundancy import (
    BRANCH_VERDICTS, BranchVerdict,
    ClassifiedBranch, classified_branches,
    classify_branch, forced_line_detection,
    low_information_rate,
    redundant_branch_rate, replay_reuse,
)
from .report import (
    V110Report, build_redundancy_artifact,
    build_report,
)


__all__ = [
    "BRANCH_VERDICTS",
    "Branch",
    "BranchVerdict",
    "ClassifiedBranch",
    "POSITION_KINDS",
    "Position",
    "PositionKind",
    "V110Report",
    "build_redundancy_artifact",
    "build_report",
    "classified_branches",
    "classify_branch",
    "critical_branch_count",
    "fixture",
    "forced_line_detection",
    "kind_counts",
    "low_information_rate",
    "mean_branching_factor",
    "no_critical_branch_dropped",
    "redundant_branch_rate",
    "replay_reuse",
    "total_branch_count",
    "verdict_distribution",
]
