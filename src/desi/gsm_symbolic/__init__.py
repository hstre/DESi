"""DESi GSM-Symbolic frame-invariance probe - G0 connector (read-only).

Network-free ingestion of locally-vendored, GSM-Symbolic-shaped fixtures
into normalised, hash-bound tasks grouped by template, ready for the
frame-invariance metrics of later phases. See
``docs/gsm_symbolic_experiment_design.md`` for the full design and the
honesty/determinism boundaries.

Self-contained by design: reuses only the pure hashing primitives from
``external_benchmarks`` and never mutates that connector's registry or
committed artifacts (see ``loader`` docstring for why).
"""
from __future__ import annotations

from .groups import (
    TemplateGroup,
    build_groups,
    grouping_integrity,
)
from .loader import (
    CLAUSE_ROLES,
    KNOWN_VARIANTS,
    PROVENANCE_OFFLINE_REFERENCE,
    GsmDataset,
    GsmInstance,
    available_datasets,
    data_dir,
    load_all,
    load_dataset,
    network_free,
)
from .normalizer import (
    NormalizedGsmTask,
    all_normalized_tasks,
    normalize_dataset,
    normalized_tasks,
    task_normalization_integrity,
)

__all__ = [
    "CLAUSE_ROLES",
    "KNOWN_VARIANTS",
    "PROVENANCE_OFFLINE_REFERENCE",
    "GsmDataset",
    "GsmInstance",
    "NormalizedGsmTask",
    "TemplateGroup",
    "all_normalized_tasks",
    "available_datasets",
    "build_groups",
    "data_dir",
    "grouping_integrity",
    "load_all",
    "load_dataset",
    "network_free",
    "normalize_dataset",
    "normalized_tasks",
    "task_normalization_integrity",
]
