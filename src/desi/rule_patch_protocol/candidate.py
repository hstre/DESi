"""PatchCandidate — the input to the v2.8 patch protocol.

A candidate is a *self-describing* record of a proposed rule patch.
The protocol runner uses it to drive every phase deterministically.
No production module is modified.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GuardDescriptor:
    """One structural guard a candidate claims to implement.

    Fields are pure descriptors so the protocol can verify them:

    * ``name``: human-readable label (e.g. "negation_marker_guard")
    * ``observable``: which input property the guard inspects
      (e.g. "premise_text_substring", "premise_kind",
      "rule_iteration_order")
    * ``forbidden_shape``: what the guard refuses (e.g.
      "premises_with_negation_marker")
    """

    name: str
    observable: str
    forbidden_shape: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "observable": self.observable,
            "forbidden_shape": self.forbidden_shape,
        }


@dataclass(frozen=True)
class PatchCandidate:
    """A proposed rule patch, ready for protocol evaluation."""

    name: str
    target_rule: str
    source_branch: str
    guards: tuple[GuardDescriptor, ...] = ()
    touched_files: tuple[str, ...] = ()
    required_artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "target_rule": self.target_rule,
            "source_branch": self.source_branch,
            "guards": [g.to_dict() for g in self.guards],
            "touched_files": list(self.touched_files),
            "required_artifacts": list(self.required_artifacts),
        }

    def fingerprint(self) -> str:
        """Deterministic 16-hex hash over the candidate payload."""
        raw = json.dumps(
            self.to_dict(),
            sort_keys=True, separators=(",", ":"), default=str,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]


__all__ = ["GuardDescriptor", "PatchCandidate"]
