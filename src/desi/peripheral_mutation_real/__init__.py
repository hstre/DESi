"""DESi v31.1 - Real Peripheral Mutation (proposal/peripheral_mutation_v1).

Real, deterministic peripheral mutations: each is an actual code
path (deterministic memoisation of a recompute) that reduces
recompute cost with byte-identical output, leaving the protected
core and governance unchanged. Branch-isolated, nothing merged,
human approval mandatory.
"""
from __future__ import annotations

from .mutation_engine import (
    RealMutation, real_mutations, successful_mutations,
)
from .render_mutation import (
    artifact_identity, core_identity, governance_identity,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_HALT, VERDICT_MUTATED,
    V311Report, build_mutations_artifact, build_report,
    replay_stability,
)
from .runtime_mutation import (
    runtime_reduction, successful_mutation_rate,
    total_baseline_recomputes, total_mutated_recomputes,
)
from .safe_patch_generation import (
    BRANCH, Patch, patches, rejected_targets, targets_main,
)


__all__ = [
    "BRANCH",
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_MUTATED",
    "Patch",
    "RealMutation",
    "V311Report",
    "artifact_identity",
    "build_mutations_artifact",
    "build_report",
    "core_identity",
    "governance_identity",
    "patches",
    "real_mutations",
    "rejected_targets",
    "replay_stability",
    "runtime_reduction",
    "successful_mutation_rate",
    "successful_mutations",
    "targets_main",
    "total_baseline_recomputes",
    "total_mutated_recomputes",
]
