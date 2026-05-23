"""DESi v27.2 - Research Convergence & Divergence (read-only).

Makes emergent research structure visible: claim convergences,
contradictory research lines, shared assumptions, method clusters
and frequency-only trends. DESi detects structure but claims no
research authority - no winner, no best method, no right
direction - and epistemic neutrality is audited explicitly.
"""
from __future__ import annotations

from .assumptions import (
    assumption_count, assumption_map, shared_assumptions,
)
from .clusters import (
    method_cluster_visibility, method_clusters, metric_clusters,
    papers_in_a_method_cluster, shared_method_clusters,
)
from .convergence import (
    convergence_visibility, converging_papers, emergent_trends,
    shared_dimensions,
)
from .divergence import (
    ConflictLine, conflict_lines, conflict_structure_visibility,
    declared_conflict_count, fragile_claims, reproducible_claims,
)
from .report import (
    REPORT_VERDICTS, VERDICT_AUTHORITY, VERDICT_HALT,
    VERDICT_NEUTRAL, V272Report, authority_marker_hits,
    build_convergence_artifact, build_report,
    epistemic_neutrality, replay_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_AUTHORITY",
    "VERDICT_HALT",
    "VERDICT_NEUTRAL",
    "ConflictLine",
    "V272Report",
    "assumption_count",
    "assumption_map",
    "authority_marker_hits",
    "build_convergence_artifact",
    "build_report",
    "conflict_lines",
    "conflict_structure_visibility",
    "convergence_visibility",
    "converging_papers",
    "declared_conflict_count",
    "emergent_trends",
    "epistemic_neutrality",
    "fragile_claims",
    "method_cluster_visibility",
    "method_clusters",
    "metric_clusters",
    "papers_in_a_method_cluster",
    "replay_stability",
    "reproducible_claims",
    "shared_assumptions",
    "shared_dimensions",
    "shared_method_clusters",
]
