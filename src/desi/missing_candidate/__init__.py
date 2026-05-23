"""DESi v3.75 — missing candidate reconstruction.

Builds structural CandidateObject records (no text)
from the v3.74 orphan-leakage centroids and compares
against the actual removed anchor's features.
"""
from __future__ import annotations

from .candidate import (
    CandidateMatch, CandidateObject,
    PRE_AUDIT_INDEX, compare_to_actual,
    reconstruct_candidate,
)
from .reconstruct import all_candidate_matches
from .report import (
    NEPTUN_MATCH_FLOOR, V375Report,
    build_missing_candidate_reconstruction_artifact,
    build_report,
)


__all__ = [
    "CandidateMatch", "CandidateObject",
    "NEPTUN_MATCH_FLOOR", "PRE_AUDIT_INDEX",
    "V375Report", "all_candidate_matches",
    "build_missing_candidate_reconstruction_artifact",
    "build_report", "compare_to_actual",
    "reconstruct_candidate",
]
