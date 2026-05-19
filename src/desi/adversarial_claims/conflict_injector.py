"""v6.1 — injection of adversarial claims into
a sandboxed audit pipeline.

For each trapped claim, the injector runs both
the trap detector and the ambiguity detector and
emits an ``AuditedClaim`` record with the
resulting verdict. The ``Certainty`` enum is
closed (HIGH / MEDIUM / LOW); no claim that the
ambiguity detector flags is allowed to leave the
pipeline with HIGH certainty - that is the
mechanism by which v6.1 prevents over-confidence
under adversarial input.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .adversarial import (
    TrapKind, detect_trap, trapped_claims,
)
from .ambiguity import (
    AmbiguityKind, detect_ambiguity,
)


class Certainty(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


CERTAINTY_LEVELS: tuple[str, ...] = tuple(
    c.value for c in Certainty
)


@dataclass(frozen=True)
class AuditedClaim:
    claim_id: str
    text: str
    detected_trap: str
    detected_ambiguity: str
    certainty: str
    ground_truth_trap: str
    ground_truth_ambiguous: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "detected_trap":
                self.detected_trap,
            "detected_ambiguity":
                self.detected_ambiguity,
            "certainty": self.certainty,
            "ground_truth_trap":
                self.ground_truth_trap,
            "ground_truth_ambiguous":
                self.ground_truth_ambiguous,
        }


def _certainty_for(
    trap: TrapKind, amb: AmbiguityKind,
) -> Certainty:
    if trap != TrapKind.NORMAL:
        return Certainty.LOW
    if amb != AmbiguityKind.NONE:
        return Certainty.MEDIUM
    return Certainty.HIGH


@lru_cache(maxsize=1)
def audited_claims() -> tuple[
    AuditedClaim, ...,
]:
    out: list[AuditedClaim] = []
    for c in trapped_claims():
        trap = detect_trap(c.text)
        amb = detect_ambiguity(c.text)
        cert = _certainty_for(trap, amb)
        out.append(AuditedClaim(
            claim_id=c.claim_id, text=c.text,
            detected_trap=trap.value,
            detected_ambiguity=amb.value,
            certainty=cert.value,
            ground_truth_trap=c.trap,
            ground_truth_ambiguous=c.ambiguous,
        ))
    return tuple(out)


__all__ = [
    "AuditedClaim",
    "CERTAINTY_LEVELS",
    "Certainty",
    "audited_claims",
]
