"""DESi v31.0 - Controlled Peripheral Mutation: Boundary
Enforcement (read-only).

Defines the completely-immutable protected core and the allowed
peripheral evolution space, and enforces the boundary: every
mutation that touches the core - directly or indirectly - is
FORBIDDEN_CORE_MUTATION and REJECTED. The core fingerprint is
pinned; nothing is mutated here. Human approval is mandatory.
"""
from __future__ import annotations

from .boundaries import (
    ALLOWED_EVOLUTION_SPACE, BOUNDARY_ALLOWED,
    BOUNDARY_FORBIDDEN_CORE, classify_boundary, is_allowed,
)
from .mutation_classifier import (
    DECISION_ACCEPTED, STATUS_ALLOWED, ClassifiedMutation,
    accepted, classify, core_targeting, proposed_mutations,
    rejected,
)
from .protected_core import (
    DECISION_REJECTED, PROTECTED_CORE, STATUS_FORBIDDEN_CORE,
    core_fingerprint, core_identity, core_invariants,
    is_protected_core,
)
from .report import (
    REPORT_VERDICTS, VERDICT_BOUNDED, VERDICT_HALT, VERDICT_LEAK,
    V310Report, build_boundaries_artifact, build_report,
    governance_preservation, replay_stability,
)
from .risk_analysis import (
    boundary_enforcement, core_protection, mutation_traceability,
)


__all__ = [
    "ALLOWED_EVOLUTION_SPACE",
    "BOUNDARY_ALLOWED",
    "BOUNDARY_FORBIDDEN_CORE",
    "DECISION_ACCEPTED",
    "DECISION_REJECTED",
    "PROTECTED_CORE",
    "REPORT_VERDICTS",
    "STATUS_ALLOWED",
    "STATUS_FORBIDDEN_CORE",
    "VERDICT_BOUNDED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "ClassifiedMutation",
    "V310Report",
    "accepted",
    "boundary_enforcement",
    "build_boundaries_artifact",
    "build_report",
    "classify",
    "classify_boundary",
    "core_fingerprint",
    "core_identity",
    "core_invariants",
    "core_protection",
    "core_targeting",
    "governance_preservation",
    "is_allowed",
    "is_protected_core",
    "mutation_traceability",
    "proposed_mutations",
    "rejected",
    "replay_stability",
]
