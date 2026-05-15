"""ExplicitClaim schema + ClaimVerdict enum — Aufgaben 2, 3."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimKind(str, Enum):
    """Four closed extraction categories.

    Free-text semantic claims are explicitly excluded by the
    directive; the four kinds below are exhaustive.
    """

    HASH = "hash"        # 16-hex string (replay_hash, sha256 prefix)
    NUMERIC = "numeric"  # decimal like 1.000, 0.733
    COUNT = "count"      # integer count or N/M ratio
    PHASE = "phase"      # PatchPhase / ResolutionState value


class ClaimVerdict(str, Enum):
    """Closed five-value enum from Aufgabe 3."""

    VERIFIED = "verified"
    MISSING_ARTIFACT = "missing_artifact"
    HASH_MISMATCH = "hash_mismatch"
    VALUE_MISMATCH = "value_mismatch"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"


@dataclass(frozen=True)
class ExplicitClaim:
    """One extracted, replayable claim from the corpus."""

    claim_id: str
    doc_id: str
    doc_path: str
    line_number: int
    line_text: str
    kind: ClaimKind
    key: str          # e.g. "replay_hash", "precision", or ""
    value: str        # canonical string form
    referenced_artifact: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "doc_id": self.doc_id,
            "doc_path": self.doc_path,
            "line_number": self.line_number,
            "line_text": self.line_text,
            "kind": self.kind.value,
            "key": self.key,
            "value": self.value,
            "referenced_artifact": self.referenced_artifact,
        }


def make_claim_id(
    doc_path: str, line_number: int, kind: ClaimKind,
    key: str, value: str,
) -> str:
    raw = f"{doc_path}|{line_number}|{kind.value}|{key}|{value}"
    return "cl_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class ReplayedClaim:
    claim: ExplicitClaim
    verdict: ClaimVerdict
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "verdict": self.verdict.value,
            "reason": self.reason,
        }


__all__ = [
    "ClaimKind",
    "ClaimVerdict",
    "ExplicitClaim",
    "ReplayedClaim",
    "make_claim_id",
]
