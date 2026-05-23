"""DESi v3.103 - T10 historical compatibility
audit.
"""
from __future__ import annotations

from .compatibility import (
    CONTRADICTION_TYPE,
    augmented_dict, augmented_vector,
    contradiction_type_for,
    contradiction_type_for_text,
    selected_candidate,
)
from .replay import (
    HistoricalGateOutcome,
    all_historical_gate_outcomes,
    beneficial_flip_count,
    compatibility_score,
    failure_class_delta,
    gate_flip_count,
    historical_auc_delta,
    replay_hash_breakage,
)
from .report import (
    HISTORICAL_AUC_DELTA_TOLERANCE,
    V3103Report,
    build_report,
    build_t10_historical_compatibility_artifact,
)


__all__ = [
    "CONTRADICTION_TYPE",
    "HISTORICAL_AUC_DELTA_TOLERANCE",
    "HistoricalGateOutcome",
    "V3103Report",
    "all_historical_gate_outcomes",
    "augmented_dict", "augmented_vector",
    "beneficial_flip_count",
    "build_report",
    "build_t10_historical_compatibility_artifact",
    "compatibility_score",
    "contradiction_type_for",
    "contradiction_type_for_text",
    "failure_class_delta",
    "gate_flip_count",
    "historical_auc_delta",
    "replay_hash_breakage",
    "selected_candidate",
]
