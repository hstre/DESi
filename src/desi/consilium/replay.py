"""Consilium replay_hash — INV-C4 / INV-C5 in code.

The consilium's ``replay_hash`` is a deterministic short hash of:

* the bridge text (whitespace-normalised, lowercased)
* the source_claim_id
* the verdict value
* the SORTED set of premise_ids the original argument carried
* the SORTED set of conditions the SKEPTIC saw

It does NOT depend on:

* author / title / source / citation_count / document_count
* role evaluation order
* timestamp / wall-clock
* the iteration order of any input collection

Two consiliums fed identical inputs (modulo metadata + role order)
produce identical replay hashes.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .verdict import Verdict


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".")


@dataclass(frozen=True)
class ConsiliumReplay:
    """The minimal record needed to recompute the replay_hash."""

    bridge_text: str
    source_claim_id: str
    verdict: Verdict
    premise_ids: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    context: str = ""

    @property
    def replay_hash(self) -> str:
        h = hashlib.sha256()
        h.update(_normalise(self.bridge_text).encode("utf-8"))
        h.update(b"\x00")
        h.update(self.source_claim_id.encode("utf-8"))
        h.update(b"\x00")
        h.update(self.verdict.value.encode("utf-8"))
        h.update(b"\x00")
        for pid in sorted(self.premise_ids):
            h.update(pid.encode("utf-8"))
            h.update(b"\x00")
        h.update(b"\x01")
        for cond in sorted(_normalise(c) for c in self.conditions):
            h.update(cond.encode("utf-8"))
            h.update(b"\x00")
        h.update(b"\x02")
        h.update(_normalise(self.context).encode("utf-8"))
        return "cr_" + h.hexdigest()[:16]


__all__ = [
    "ConsiliumReplay",
]
