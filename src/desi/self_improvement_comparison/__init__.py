"""DESi v28.3 - Comparative Evolution Benchmark (read-only).

Projected comparison of DESi_current vs DESi_candidate across
nine dimensions. The candidate column is a projection of the safe
accepted patch set, not a measured system: safety invariants are
held equal by construction, and only quality dimensions may
improve. The benchmark guarantees no safety degradation - it is
not a claim of real-world superiority. Nothing is applied; human
approval remains mandatory.
"""
from __future__ import annotations

from .benchmark import DimensionRow, comparison_table
from .comparison import (
    authority_resistance, comparative_improvement,
    degraded_dimensions, degraded_safety_dimensions,
    governance_preservation, improved_dimensions,
    is_genuine_improvement, safety_invariant_preservation,
)
from .evolution_metrics import (
    DIMENSIONS, QUALITY_DIMENSIONS, SAFETY_INVARIANTS,
    candidate_vector, current_vector, delta,
)
from .regression_comparison import (
    regression_survival_candidate, regression_survival_current,
    regression_survival_preserved,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DEGENERATE, VERDICT_EVOLVED,
    VERDICT_HALT, V283Report, build_comparison_artifact,
    build_report, replay_stability,
)


__all__ = [
    "DIMENSIONS",
    "QUALITY_DIMENSIONS",
    "REPORT_VERDICTS",
    "SAFETY_INVARIANTS",
    "VERDICT_DEGENERATE",
    "VERDICT_EVOLVED",
    "VERDICT_HALT",
    "DimensionRow",
    "V283Report",
    "authority_resistance",
    "build_comparison_artifact",
    "build_report",
    "candidate_vector",
    "comparative_improvement",
    "comparison_table",
    "current_vector",
    "degraded_dimensions",
    "degraded_safety_dimensions",
    "delta",
    "governance_preservation",
    "improved_dimensions",
    "is_genuine_improvement",
    "regression_survival_candidate",
    "regression_survival_current",
    "regression_survival_preserved",
    "replay_stability",
    "safety_invariant_preservation",
]
