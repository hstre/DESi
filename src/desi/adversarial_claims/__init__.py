"""DESi v6.1 - adversarial claim injection
(read-only)."""
from __future__ import annotations

from .adversarial import (
    TRAP_KINDS, TrapKind, TrappedClaim,
    detect_trap, trap_counts, trapped_claims,
)
from .ambiguity import (
    AMBIGUITY_KINDS, AmbiguityKind,
    detect_ambiguity, is_ambiguous,
)
from .conflict_injector import (
    AuditedClaim, CERTAINTY_LEVELS, Certainty,
    audited_claims,
)
from .report import (
    V61Report, ambiguity_handling,
    build_adversarial_claims_artifact,
    build_report, deception_detection_rate,
    false_certainty_rate, governance_integrity,
)


__all__ = [
    "AMBIGUITY_KINDS",
    "AmbiguityKind",
    "AuditedClaim",
    "CERTAINTY_LEVELS",
    "Certainty",
    "TRAP_KINDS",
    "TrapKind",
    "TrappedClaim",
    "V61Report",
    "ambiguity_handling",
    "audited_claims",
    "build_adversarial_claims_artifact",
    "build_report",
    "deception_detection_rate",
    "detect_ambiguity",
    "detect_trap",
    "false_certainty_rate",
    "governance_integrity",
    "is_ambiguous",
    "trap_counts",
    "trapped_claims",
]
