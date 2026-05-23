"""desi.release_validation - final public-release readiness audit.

A hard, read-only seven-phase audit of the main branch. Any blocker
(replay drift, artifact mismatch, hidden state, fake example, broken
import, stale README section, inconsistent metrics, undocumented
dependency, timestamps in artifacts) forces MAIN_BRANCH_NOT_READY.
DESi audits itself for release-readiness; it does not approve itself.
"""
from __future__ import annotations

from .documents import (
    all_documents, build_ci_integrity, build_clean_room_install,
    build_example_execution, build_main_branch_verdict,
    build_readme_consistency, build_replay_integrity,
    build_reviewer_attack_surface,
)
from .report import (
    VERDICT_NOT_READY, VERDICT_READY, blockers,
    declared_dependencies, phase1_clean_room,
    phase2_replay_integrity, phase3_readme_consistency,
    phase4_examples, phase5_ci_integrity, resolved_during_audit,
    reviewer_attack_surface, undocumented_dependencies, verdict,
)

__all__ = [
    "VERDICT_NOT_READY",
    "VERDICT_READY",
    "all_documents",
    "blockers",
    "build_ci_integrity",
    "build_clean_room_install",
    "build_example_execution",
    "build_main_branch_verdict",
    "build_readme_consistency",
    "build_replay_integrity",
    "build_reviewer_attack_surface",
    "declared_dependencies",
    "phase1_clean_room",
    "phase2_replay_integrity",
    "phase3_readme_consistency",
    "phase4_examples",
    "phase5_ci_integrity",
    "resolved_during_audit",
    "reviewer_attack_surface",
    "undocumented_dependencies",
    "verdict",
]
