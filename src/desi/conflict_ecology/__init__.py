"""DESi v6.2 - multi-paper conflict ecology
(read-only)."""
from __future__ import annotations

from .conflict_graph import (
    GraphNode, coherence_score, components,
    conflict_resolution_stability,
    fragmentation_rate, nodes,
    polarization_index,
    topic_conflict_density,
)
from .cross_paper import (
    CrossPaperConflict,
    ECOLOGY_CONFLICT_KINDS,
    EcologyConflictKind, EcologyPaper, corpus,
    detected_conflicts, detection_precision,
    detection_recall, ground_truth_conflicts,
)
from .ecology import (
    TopicCluster, component_sizes,
    conflict_kind_counts, school_distribution,
    topic_clusters, uncertainty_zone_count,
)
from .report import (
    V62Report, build_conflict_ecology_artifact,
    build_report,
)


__all__ = [
    "CrossPaperConflict",
    "ECOLOGY_CONFLICT_KINDS",
    "EcologyConflictKind",
    "EcologyPaper",
    "GraphNode",
    "TopicCluster",
    "V62Report",
    "build_conflict_ecology_artifact",
    "build_report",
    "coherence_score",
    "component_sizes",
    "components",
    "conflict_kind_counts",
    "conflict_resolution_stability",
    "corpus",
    "detected_conflicts",
    "detection_precision",
    "detection_recall",
    "fragmentation_rate",
    "ground_truth_conflicts",
    "nodes",
    "polarization_index",
    "school_distribution",
    "topic_clusters",
    "topic_conflict_density",
    "uncertainty_zone_count",
]
