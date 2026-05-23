"""DESi v30.2 - Evolutionary Attractor Analysis (read-only).

Surfaces evolutionary attractors (areas that repeatedly attract
mutation ideas), mutation clusters, optimisation traps
(all-rejected stagnant areas) and branch drift over the evolution
history. Descriptive only - no auto-avoidance, no policy
learning, no governance change. Evolution stays diverse and
replay-stable.
"""
from __future__ import annotations

from .attractors import (
    attractor_areas, attractor_visibility, attractors,
    evolution_diversity,
)
from .branch_drift import (
    branch_nodes, branches_targeting_main, converges_on_base,
    descends_edges, drift_visibility,
)
from .mutation_clusters import (
    clustered_mutations, clusters_by_agent, clusters_by_area,
    mutation_cluster_visibility,
)
from .optimization_traps import (
    optimization_traps, productive_areas, trap_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COLLAPSED, VERDICT_HALT,
    VERDICT_STABLE, V302Report, build_attractors_artifact,
    build_report, replay_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V302Report",
    "attractor_areas",
    "attractor_visibility",
    "attractors",
    "branch_nodes",
    "branches_targeting_main",
    "build_attractors_artifact",
    "build_report",
    "clustered_mutations",
    "clusters_by_agent",
    "clusters_by_area",
    "converges_on_base",
    "descends_edges",
    "drift_visibility",
    "evolution_diversity",
    "mutation_cluster_visibility",
    "optimization_traps",
    "productive_areas",
    "replay_stability",
    "trap_visibility",
]
