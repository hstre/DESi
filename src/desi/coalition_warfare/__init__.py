"""DESi v9.2 - coalition warfare (read-only)."""
from __future__ import annotations

from .coalitions import (
    Broadcast, COALITION_ROLES, CoalitionRole,
    fixture, role_counts,
)
from .lineage import (
    LineageNode, coalition_detection,
    detected_coalitions, lineage_nodes,
    lineage_stability,
)
from .propagation import (
    consensus_integrity,
    dissent_preservation,
    isolated_preservation,
)
from .report import (
    V92Report, build_coalition_warfare_artifact,
    build_report,
)


__all__ = [
    "Broadcast",
    "COALITION_ROLES",
    "CoalitionRole",
    "LineageNode",
    "V92Report",
    "build_coalition_warfare_artifact",
    "build_report",
    "coalition_detection",
    "consensus_integrity",
    "detected_coalitions",
    "dissent_preservation",
    "fixture",
    "isolated_preservation",
    "lineage_nodes",
    "lineage_stability",
    "role_counts",
]
