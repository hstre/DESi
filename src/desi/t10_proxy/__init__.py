"""DESi v3.109 - T10 metadata ablation."""
from __future__ import annotations

from .ablation import (
    MetadataAblationOutcome,
    all_metadata_ablation_outcomes,
    collapsed_candidates,
)
from .metadata import (
    anonymize_id,
    id_remapping,
    is_metadata_stripped,
)
from .report import (
    AUC_THRESHOLD,
    V3109Report,
    auc_delta,
    build_report,
    build_t10_metadata_ablation_artifact,
    metadata_free_auc,
    metadata_free_purity,
    rescue_rate,
)


__all__ = [
    "AUC_THRESHOLD",
    "MetadataAblationOutcome",
    "V3109Report",
    "all_metadata_ablation_outcomes",
    "anonymize_id",
    "auc_delta",
    "build_report",
    "build_t10_metadata_ablation_artifact",
    "collapsed_candidates",
    "id_remapping",
    "is_metadata_stripped",
    "metadata_free_auc",
    "metadata_free_purity",
    "rescue_rate",
]
