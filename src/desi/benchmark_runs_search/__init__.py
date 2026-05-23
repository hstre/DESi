"""DESi v34.1 - Search Compression Benchmark Run (read-only).

Executes a search-compression task through the v33 search adapter and
reports the measured reduction together with the preservation of
critical branches, novelty and quality. Critical branches stay
visible and are never hard-pruned.
"""
from __future__ import annotations

from .branch_preservation import (
    aspect_breakdown, critical_branch_count, critical_branches_safe,
    hard_pruned_count, low_information_branch_count,
    novelty_branch_count, redundant_branch_count, replay_reuse_count,
    soft_reweighted_count,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V341Report, build_report, build_search_run_artifact,
    critical_branch_preservation, node_reduction,
    novelty_preservation, quality_preservation, replay_stability,
    search_run_metrics,
)
from .scorecard import (
    SearchScorecard, scorecard_traceable, search_scorecard,
)
from .search_runner import metric, metrics, run
from .search_tasks import SEARCH_RUN_ASPECTS, search_task


__all__ = [
    "REPORT_VERDICTS",
    "SEARCH_RUN_ASPECTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "SearchScorecard",
    "V341Report",
    "aspect_breakdown",
    "build_report",
    "build_search_run_artifact",
    "critical_branch_count",
    "critical_branch_preservation",
    "critical_branches_safe",
    "hard_pruned_count",
    "low_information_branch_count",
    "metric",
    "metrics",
    "node_reduction",
    "novelty_branch_count",
    "novelty_preservation",
    "quality_preservation",
    "redundant_branch_count",
    "replay_reuse_count",
    "replay_stability",
    "run",
    "scorecard_traceable",
    "search_run_metrics",
    "search_scorecard",
    "search_task",
    "soft_reweighted_count",
]
