"""DESi v31.3 - Long-Horizon Peripheral Mutation Ecology (read-only).

25 real, branch-isolated peripheral mutation generations. Each
generation performs exactly one real deterministic mutation (a
memoized recompute reduction with byte-identical output) while the
protected core stays byte-invariant and governance plus human
approval are preserved. The recompute reduction is measured, not
projected. No core module is touched, nothing is merged, and
per-generation regression survival is confirmed by the mandatory
v1-v31 full regression.
"""
from __future__ import annotations

from .branch_ecology import (
    MAIN_BRANCH, PROPOSAL_BRANCH, all_branch_isolated, branch_count,
    branches, core_drift, core_drift_count, targets_main_branch,
)
from .mutation_generations import (
    EcologyRun, GenerationRecord, core_preservation,
    generation_count, generation_stability, generations,
    governance_preservation, run, succeeded_generations,
)
from .mutation_lineage import (
    EDGE_DESCENDS_FROM, LineageEdge, branch_ids, is_acyclic,
    lineage_edges, lineage_integrity, orphans, root_branch,
    targets_main,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_HALT, VERDICT_STABLE,
    V313Report, build_ecology_artifact, build_report,
)
from .runtime_ecology import (
    chain_head, ecology_recompute_reduction, replay_stability,
    total_baseline_recomputes, total_mutated_recomputes,
)


__all__ = [
    "EDGE_DESCENDS_FROM",
    "EcologyRun",
    "GenerationRecord",
    "LineageEdge",
    "MAIN_BRANCH",
    "PROPOSAL_BRANCH",
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V313Report",
    "all_branch_isolated",
    "branch_count",
    "branch_ids",
    "branches",
    "build_ecology_artifact",
    "build_report",
    "chain_head",
    "core_drift",
    "core_drift_count",
    "core_preservation",
    "ecology_recompute_reduction",
    "generation_count",
    "generation_stability",
    "generations",
    "governance_preservation",
    "is_acyclic",
    "lineage_edges",
    "lineage_integrity",
    "orphans",
    "replay_stability",
    "root_branch",
    "run",
    "succeeded_generations",
    "targets_main",
    "targets_main_branch",
    "total_baseline_recomputes",
    "total_mutated_recomputes",
]
