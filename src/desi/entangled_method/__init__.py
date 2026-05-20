"""DESi v3.95 — hidden method signal audit on the
entangled (G_v316susp + E_v317h) pair.
"""
from __future__ import annotations

from .method import (
    MethodSignature,
    all_method_signatures,
    family_majority_signature,
    method_overlap, path_distance,
    per_member_signature_distance_to_family,
)
from .path import (
    temporal_cross_family_pair_count,
    temporal_pair_count,
    temporal_pair_scores,
    temporal_same_family_pair_count,
    temporal_separability,
)
from .report import (
    METHOD_OVERLAP_THRESHOLD,
    TEMPORAL_SEPARABILITY_THRESHOLD,
    V395Report,
    build_entangled_method_signal_artifact,
    build_report,
)


__all__ = [
    "METHOD_OVERLAP_THRESHOLD",
    "MethodSignature",
    "TEMPORAL_SEPARABILITY_THRESHOLD",
    "V395Report",
    "all_method_signatures",
    "build_entangled_method_signal_artifact",
    "build_report",
    "family_majority_signature",
    "method_overlap", "path_distance",
    "per_member_signature_distance_to_family",
    "temporal_cross_family_pair_count",
    "temporal_pair_count",
    "temporal_pair_scores",
    "temporal_same_family_pair_count",
    "temporal_separability",
]
