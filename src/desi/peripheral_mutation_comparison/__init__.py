"""DESi v31.2 - Comparative Peripheral Evolution (read-only).

A real, measured comparison of DESi_current vs
DESi_peripheral_mutation_v1: a runtime improvement (measured
recompute reduction, not projected) with the protected core and
governance byte-identical and replay stable. Branch-isolated,
nothing merged, human approval mandatory.
"""
from __future__ import annotations

from .artifact_comparison import (
    all_outputs_identical, artifact_identity_score,
)
from .comparison import (
    core_identity, governance_identity, measured_improvement,
    regression_survival, replay_stability,
)
from .governance_diff import core_diff
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_HALT, VERDICT_REAL,
    V312Report, build_comparison_artifact, build_report,
)
from .runtime_analysis import (
    baseline_recomputes, mutated_recomputes,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "V312Report",
    "all_outputs_identical",
    "artifact_identity_score",
    "baseline_recomputes",
    "build_comparison_artifact",
    "build_report",
    "core_diff",
    "core_identity",
    "governance_identity",
    "measured_improvement",
    "mutated_recomputes",
    "regression_survival",
    "replay_stability",
]
