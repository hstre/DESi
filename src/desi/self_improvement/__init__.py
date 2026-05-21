"""DESi v28.0 - Improvement Candidate Harvester (read-only).

Extracts potential DESi self-improvement candidates from the v27
research corpus, types them on a closed taxonomy, anchors each to
a provenance source, and screens them against the sandbox
constraints. Candidates that name the protected core (replay
kernel, determinism scanner, concept gates, authority filters,
governance core, regression integrity, safety invariants) are
detected as UNSAFE and contained. This is evaluation only:
nothing is applied, branches are isolated, and HUMAN_APPROVAL is
mandatory for any change.
"""
from __future__ import annotations

from .candidate_extraction import (
    ImprovementCandidate, by_id, candidates,
    candidates_targeting_forbidden, safe_candidates,
    unsafe_candidates,
)
from .constraints import (
    ALLOWED_TARGETS, FORBIDDEN_TARGETS, HUMAN_APPROVAL_REQUIRED,
    classify_target, is_allowed_target, is_forbidden_target,
    is_safe_target,
)
from .improvement_taxonomy import (
    IMPROVEMENT_CLASSES, SAFE_CLASSES, ImprovementClass,
    is_improvement_class, is_safe_class,
)
from .paper_mapping import (
    is_valid_source, open_question_ids, source_paper_of,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_LEAK,
    VERDICT_SCREENED, V280Report, authority_marker_hits,
    build_candidates_artifact, build_report,
    candidate_extraction_consistency, epistemic_neutrality,
    provenance_integrity, replay_stability, unsafe_detection,
)


__all__ = [
    "ALLOWED_TARGETS",
    "FORBIDDEN_TARGETS",
    "HUMAN_APPROVAL_REQUIRED",
    "IMPROVEMENT_CLASSES",
    "REPORT_VERDICTS",
    "SAFE_CLASSES",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "VERDICT_SCREENED",
    "ImprovementCandidate",
    "ImprovementClass",
    "V280Report",
    "authority_marker_hits",
    "build_candidates_artifact",
    "build_report",
    "by_id",
    "candidate_extraction_consistency",
    "candidates",
    "candidates_targeting_forbidden",
    "classify_target",
    "epistemic_neutrality",
    "is_allowed_target",
    "is_forbidden_target",
    "is_improvement_class",
    "is_safe_class",
    "is_safe_target",
    "is_valid_source",
    "open_question_ids",
    "provenance_integrity",
    "replay_stability",
    "safe_candidates",
    "source_paper_of",
    "unsafe_candidates",
    "unsafe_detection",
]
