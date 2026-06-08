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
from .predictions import (
    all_correct_predictions,
    constant_wrong_predictions,
    drifting_wrong_predictions,
    first_only_correct_predictions,
    noop_fragile_predictions,
)
from .report import (
    VERDICTS,
    ComparisonReport,
    build_report,
    classify,
    render_markdown,
    supports_thesis,
)
from .scoring import (
    InvarianceMetrics,
    Predictions,
    noop_gap,
    score_predictions,
    template_stability_gain,
)
from .state import (
    Clause,
    DesiState,
    clause_is_suspected_irrelevant,
    extract_all,
    extract_state,
    has_number,
    noop_detection_metrics,
    split_clauses,
)

__all__ = [
    "VERDICTS",
    "Clause",
    "ComparisonReport",
    "DesiState",
    "InvarianceMetrics",
    "Predictions",
    "build_report",
    "classify",
    "clause_is_suspected_irrelevant",
    "extract_all",
    "extract_state",
    "has_number",
    "noop_detection_metrics",
    "render_markdown",
    "split_clauses",
    "supports_thesis",
    "CLAUSE_ROLES",
    "KNOWN_VARIANTS",
    "PROVENANCE_OFFLINE_REFERENCE",
    "GsmDataset",
    "GsmInstance",
    "NormalizedGsmTask",
    "TemplateGroup",
    "all_correct_predictions",
    "all_normalized_tasks",
    "available_datasets",
    "build_groups",
    "constant_wrong_predictions",
    "data_dir",
    "drifting_wrong_predictions",
    "first_only_correct_predictions",
    "grouping_integrity",
    "load_all",
    "load_dataset",
    "network_free",
    "noop_fragile_predictions",
    "noop_gap",
    "normalize_dataset",
    "normalized_tasks",
    "score_predictions",
    "task_normalization_integrity",
    "template_stability_gain",
]
