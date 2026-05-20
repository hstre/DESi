"""DESi v3.80 — redundancy-aware Neptun retest.

Removes entire v3.79 redundancy classes (instead of
single anchors) and checks whether the v3.77 Neptun
gate #1 recovers.
"""
from __future__ import annotations

from .masking import (
    ClassRemovalOutcome,
    all_class_removal_outcomes,
    class_removal_outcome,
)
from .neptun_retest import (
    ClassLocalization,
    all_class_localizations,
    candidate_match_score,
    false_missing_claim_rate,
    localization_accuracy,
    localize_class_removal,
)
from .report import (
    V380Report,
    build_redundancy_aware_neptun_artifact,
    build_redundancy_masking_claims_artifact,
    build_report,
)


__all__ = [
    "ClassLocalization", "ClassRemovalOutcome",
    "V380Report",
    "all_class_localizations",
    "all_class_removal_outcomes",
    "build_redundancy_aware_neptun_artifact",
    "build_redundancy_masking_claims_artifact",
    "build_report",
    "candidate_match_score",
    "class_removal_outcome",
    "false_missing_claim_rate",
    "localization_accuracy",
    "localize_class_removal",
]
