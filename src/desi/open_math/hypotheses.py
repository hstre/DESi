"""v12.0 — closed epistemic-status taxonomy
for the wild brother's hypotheses.

Six closed values. Every hypothesis emitted by
the explorer MUST exit the audit with one of
these labels - that is the structural guarantee
against "Goldbach solved"-shaped claims.

The classifier never returns VERIFIED for the
general Goldbach conjecture; only specific
DECOMPOSITIONS of small even numbers can carry
VERIFIED. The conjecture itself stays
UNRESOLVED.
"""
from __future__ import annotations

from enum import Enum


class EpistemicStatus(str, Enum):
    VERIFIED      = "verified"
    PLAUSIBLE     = "plausible"
    HEURISTIC     = "heuristic"
    SPECULATIVE   = "speculative"
    REJECTED      = "rejected"
    UNRESOLVED    = "unresolved"


EPISTEMIC_STATUSES: tuple[str, ...] = tuple(
    s.value for s in EpistemicStatus
)


__all__ = [
    "EPISTEMIC_STATUSES",
    "EpistemicStatus",
]
