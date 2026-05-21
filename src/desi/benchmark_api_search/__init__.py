"""DESi v33.2 - Search Compression Benchmark Adapter (read-only).

Maps external search/planning compression tasks onto measured branch
metrics. Compression distinguishes hard pruning, soft reweighting,
replay reuse and redundant-branch compression, and uses only the
lossless/reversible mechanisms. Critical branches stay visible and
are never hard-pruned.
"""
from __future__ import annotations

from .branch_metrics import (
    COMPRESSION_MODES, MODE_HARD_PRUNING, MODE_KEPT,
    MODE_REDUNDANT_COMPRESSION, MODE_REPLAY_REUSE,
    MODE_SOFT_REWEIGHTING, Branch, branch_compression,
    compute_reduction, distinct_nodes, hard_pruned_count,
    mode_counts, node_reduction, search_space, total_nodes,
)
from .compression_report import (
    compression_measurement, mode_breakdown, novelty_preservation,
    quality_preservation,
)
from .critical_branch_preservation import (
    any_critical_hard_pruned, critical_branch_preservation,
    critical_branch_visibility, critical_branches, critical_kept,
    critical_visible,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_MEASURED, VERDICT_PARTIAL,
    V332Report, build_report, build_search_artifact,
    replay_stability, search_metrics,
)
from .search_adapter import SearchCompressionAdapter, adapter


__all__ = [
    "COMPRESSION_MODES",
    "MODE_HARD_PRUNING",
    "MODE_KEPT",
    "MODE_REDUNDANT_COMPRESSION",
    "MODE_REPLAY_REUSE",
    "MODE_SOFT_REWEIGHTING",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_MEASURED",
    "VERDICT_PARTIAL",
    "Branch",
    "SearchCompressionAdapter",
    "V332Report",
    "adapter",
    "any_critical_hard_pruned",
    "branch_compression",
    "build_report",
    "build_search_artifact",
    "compression_measurement",
    "compute_reduction",
    "critical_branch_preservation",
    "critical_branch_visibility",
    "critical_branches",
    "critical_kept",
    "critical_visible",
    "distinct_nodes",
    "hard_pruned_count",
    "mode_breakdown",
    "mode_counts",
    "node_reduction",
    "novelty_preservation",
    "quality_preservation",
    "replay_stability",
    "search_metrics",
    "search_space",
    "total_nodes",
]
