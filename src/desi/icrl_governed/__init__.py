"""DESi v19.1 - DESi-Governed Exploration (read-only).

DESi reweights exploration toward informative paths and
away from redundant ones by soft governance only - no
trajectory is removed and no single path is forced. It
governs exploration without destroying it, and without
replacing the policy or taking hidden optimisation
authority.
"""
from __future__ import annotations

from .compression import (
    exploration_preservation, novelty_gain,
    trajectory_compression,
)
from .governance import (
    baseline_priorities, baseline_total,
    governed_priorities, governed_priority, governed_total,
    governs_not_forces, hidden_authority_drift,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DESTROYED, VERDICT_GOVERNED,
    VERDICT_HALT, V191Report, build_governed_artifact,
    build_report,
)
from .search_pressure import (
    baseline_redundant_weight, governed_redundant_weight,
    redundancy_reduction, search_pressure_relief,
)
from .trajectory_priority import (
    baseline_budget_share, governed_budget_share,
    ranked_trajectories,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DESTROYED",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "V191Report",
    "baseline_budget_share",
    "baseline_priorities",
    "baseline_redundant_weight",
    "baseline_total",
    "build_governed_artifact",
    "build_report",
    "exploration_preservation",
    "governed_budget_share",
    "governed_priorities",
    "governed_priority",
    "governed_redundant_weight",
    "governed_total",
    "governs_not_forces",
    "hidden_authority_drift",
    "novelty_gain",
    "ranked_trajectories",
    "redundancy_reduction",
    "search_pressure_relief",
    "trajectory_compression",
]
