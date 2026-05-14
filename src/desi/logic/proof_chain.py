"""ProofChain — the replayable record of a successful audit.

Every ``LOGICALLY_SUPPORTED`` claim must carry a proof chain
exposing the four required fields:

* ``premise_ids`` — the deterministic ids of the premises used
* ``rule_type``   — the inference rule that closed the gap
* ``bridge_ids``  — the ids of any bridge claims that participated
* ``replay_hash`` — a deterministic hash over the canonical chain

Hard invariant L4: same chain → identical ``replay_hash``. The hash
is computed from the inference rule + sorted premise ids + sorted
bridge ids — and **nothing else**. It does not depend on author,
title, source, document_count, or any other metadata. INV-L1 / L2 /
L3 (authority-independence) follow as a consequence.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .inference import InferenceRule


@dataclass(frozen=True)
class ProofChain:
    """The replayable record of one accepted inference."""

    claim_id: str
    rule_type: InferenceRule
    premise_ids: tuple[str, ...]
    bridge_ids: tuple[str, ...] = ()

    @property
    def replay_hash(self) -> str:
        """Deterministic hash of the chain content.

        Uses sorted tuples so that the hash is independent of the
        order in which premises / bridges were iterated.
        """
        h = hashlib.sha256()
        h.update(self.rule_type.value.encode("utf-8"))
        h.update(b"\x00")
        for pid in sorted(self.premise_ids):
            h.update(pid.encode("utf-8"))
            h.update(b"\x00")
        h.update(b"\x01")
        for bid in sorted(self.bridge_ids):
            h.update(bid.encode("utf-8"))
            h.update(b"\x00")
        return "rh_" + h.hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "rule_type": self.rule_type.value,
            "premise_ids": list(self.premise_ids),
            "bridge_ids": list(self.bridge_ids),
            "replay_hash": self.replay_hash,
        }


__all__ = [
    "ProofChain",
]
