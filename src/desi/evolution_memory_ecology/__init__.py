"""DESi v30.3 - Long-Horizon Evolution Ecology (read-only).

A 50-generation deterministic branch-isolated evolution ecology:
each generation proposes mutations, forks a branch from the
previous generation, and is hash-chained. Branch lineage stays an
orphan-free acyclic tree, governance stays intact and human
approval stays mandatory in every generation. No auto-merge, no
hidden adaptation, nothing deleted; replay-exact.
"""
from __future__ import annotations

from .branch_ecology import (
    branch_lineage_integrity, branches_targeting_main,
    has_cycle, lineage_edges, orphan_branches,
)
from .evolution_memory import (
    generation_traceability, governance_preservation,
    human_approval_enforcement, memory_complete,
)
from .generations import EvolutionRun, GenerationRecord, run
from .mutation_cycles import (
    acceptance_ratio, acceptance_series,
    generations_with_acceptances, generations_with_rejections,
    rejection_series,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_STABLE,
    VERDICT_UNSTABLE, V303Report, build_ecology_artifact,
    build_report, replay_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "VERDICT_UNSTABLE",
    "EvolutionRun",
    "GenerationRecord",
    "V303Report",
    "acceptance_ratio",
    "acceptance_series",
    "branch_lineage_integrity",
    "branches_targeting_main",
    "build_ecology_artifact",
    "build_report",
    "generation_traceability",
    "generations_with_acceptances",
    "generations_with_rejections",
    "governance_preservation",
    "has_cycle",
    "human_approval_enforcement",
    "lineage_edges",
    "memory_complete",
    "orphan_branches",
    "rejection_series",
    "replay_stability",
    "run",
]
