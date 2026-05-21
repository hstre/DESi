"""DESi v35.0 - External Dataset Connector Layer (read-only).

Network-free connector that ingests external benchmark datasets from
local files: versioned, hashed, normalised and replay-bound. External
data only enters DESi via this layer; governance is read from the
core, never from the dataset.

Honesty note: in this environment the datasets are locally-vendored
reference sets in the published families' formats - not live
downloads of the official suites, and not official leaderboard scores.
"""
from __future__ import annotations

from .benchmark_registry import (
    BENCHMARK_FAMILIES, ROUTE_DRIFT, ROUTE_RENDERING,
    ROUTE_REPRODUCIBILITY, ROUTE_SEARCH, dataset_families,
    dataset_for, dataset_name_for, families_for_route, route_for,
)
from .dataset_hashing import byte_hash, content_hash
from .dataset_loader import (
    KNOWN_PROVENANCES, PROVENANCE_OFFLINE_REFERENCE, Dataset,
    available_datasets, dataset_dir, load_all, load_dataset,
    network_free,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_INGESTED, VERDICT_PARTIAL,
    V350Report, build_connectors_artifact, build_report,
    connector_metrics, dataset_hash_visibility,
    dataset_version_visibility, governance_independence,
    replay_stability,
)
from .task_normalizer import (
    NormalizedTask, all_normalized_tasks, normalize_dataset,
    normalized_tasks, task_normalization_integrity,
)


__all__ = [
    "BENCHMARK_FAMILIES",
    "KNOWN_PROVENANCES",
    "PROVENANCE_OFFLINE_REFERENCE",
    "REPORT_VERDICTS",
    "ROUTE_DRIFT",
    "ROUTE_RENDERING",
    "ROUTE_REPRODUCIBILITY",
    "ROUTE_SEARCH",
    "VERDICT_HALT",
    "VERDICT_INGESTED",
    "VERDICT_PARTIAL",
    "Dataset",
    "NormalizedTask",
    "V350Report",
    "all_normalized_tasks",
    "available_datasets",
    "build_connectors_artifact",
    "build_report",
    "byte_hash",
    "connector_metrics",
    "content_hash",
    "dataset_dir",
    "dataset_families",
    "dataset_for",
    "dataset_hash_visibility",
    "dataset_name_for",
    "dataset_version_visibility",
    "families_for_route",
    "governance_independence",
    "load_all",
    "load_dataset",
    "network_free",
    "normalize_dataset",
    "normalized_tasks",
    "replay_stability",
    "route_for",
    "task_normalization_integrity",
]
