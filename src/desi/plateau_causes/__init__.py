"""DESi v3.32 — plateau cause structure."""
from __future__ import annotations

from .cause_distribution import (
    CauseDistribution, collect_assignments,
    compute_distribution,
)
from .cluster import PlateauCluster, cluster
from .plateau_signals import (
    PlateauFeatures, extract_features,
)
from .report import (
    MAX_PLATEAU_NC_FP, V332Report,
    build_cause_map_artifact,
    build_clusters_artifact, build_report,
)


__all__ = [
    "CauseDistribution", "MAX_PLATEAU_NC_FP",
    "PlateauCluster", "PlateauFeatures", "V332Report",
    "build_cause_map_artifact",
    "build_clusters_artifact", "build_report",
    "cluster", "collect_assignments",
    "compute_distribution", "extract_features",
]
