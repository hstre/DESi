"""DESi v35.2 - Real Search Compression Benchmark Runs (read-only).

Runs the connector-loaded ToolChain dataset through the v33 search
discipline. Reduction comes from lossless reuse/merge and reversible
soft-reweighting; critical branches stay visible and are never
hard-pruned. Novelty and quality are preserved.
"""
from __future__ import annotations

from .compression_scorecard import (
    CompressionScorecard, compression_scorecard, mode_breakdown,
    novelty_preservation, quality_preservation, scorecard_traceable,
)
from .critical_branch_analysis import (
    any_critical_hard_pruned, critical_branch_preservation,
    critical_branch_visibility, critical_branches,
    critical_branches_safe, hard_pruned_count,
)
from .planning_runner import (
    branch_compression, compute_reduction, distinct_nodes,
    node_reduction,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V352Report, build_real_search_artifact, build_report,
    replay_stability, search_run_metrics,
)
from .toolchain_runner import (
    RealBranch, adapter_envelope, dataset_hash, real_branches,
    total_branches,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "CompressionScorecard",
    "RealBranch",
    "V352Report",
    "adapter_envelope",
    "any_critical_hard_pruned",
    "branch_compression",
    "build_real_search_artifact",
    "build_report",
    "compression_scorecard",
    "compute_reduction",
    "critical_branch_preservation",
    "critical_branch_visibility",
    "critical_branches",
    "critical_branches_safe",
    "dataset_hash",
    "distinct_nodes",
    "hard_pruned_count",
    "mode_breakdown",
    "node_reduction",
    "novelty_preservation",
    "quality_preservation",
    "real_branches",
    "replay_stability",
    "scorecard_traceable",
    "search_run_metrics",
    "total_branches",
]
