"""DESi v3.0 self-paper audit — read-only over docs + artifacts."""
from __future__ import annotations

from .claim import (
    ClaimKind,
    ClaimVerdict,
    ExplicitClaim,
    ReplayedClaim,
    make_claim_id,
)
from .contradictions import Contradiction, find_contradictions
from .corpus import (
    DEFAULT_DOC_ROOTS,
    DocumentArtifact,
    REQUIRED_MEMORY_DOCS,
    REQUIRED_PROTOCOL_DOCS,
    index_corpus,
    index_document,
)
from .drift import DriftFinding, find_drift
from .extractor import extract_claims_from_text
from .replayer import replay_claims
from .report import (
    SelfAuditReport,
    build_audit_report,
    compute_audit_replay_hash,
)
from .runner import SelfAuditRunner

__all__ = [
    "ClaimKind",
    "ClaimVerdict",
    "Contradiction",
    "DEFAULT_DOC_ROOTS",
    "DocumentArtifact",
    "DriftFinding",
    "ExplicitClaim",
    "REQUIRED_MEMORY_DOCS",
    "REQUIRED_PROTOCOL_DOCS",
    "ReplayedClaim",
    "SelfAuditReport",
    "SelfAuditRunner",
    "build_audit_report",
    "compute_audit_replay_hash",
    "extract_claims_from_text",
    "find_contradictions",
    "find_drift",
    "index_corpus",
    "index_document",
    "make_claim_id",
    "replay_claims",
]
