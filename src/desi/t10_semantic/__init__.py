"""DESi v3.111 - T10 semantic substitution."""
from __future__ import annotations

from .report import (
    RECOVERY_THRESHOLD,
    V3111Report,
    build_report,
    build_t10_semantic_substitution_artifact,
)
from .semantic import (
    SEMANTIC_CANDIDATES,
    SemanticCandidate,
    semantic_value,
)
from .substitute import (
    SemanticOutcome,
    all_semantic_outcomes,
    complexity_delta,
    semantic_auc,
    semantic_purity,
    semantic_recovery,
)


__all__ = [
    "RECOVERY_THRESHOLD",
    "SEMANTIC_CANDIDATES",
    "SemanticCandidate",
    "SemanticOutcome",
    "V3111Report",
    "all_semantic_outcomes",
    "build_report",
    "build_t10_semantic_substitution_artifact",
    "complexity_delta",
    "semantic_auc",
    "semantic_purity",
    "semantic_recovery",
    "semantic_value",
]
