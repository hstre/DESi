"""v7.0 — frame composition and certainty
assignment under narrative pressure.

The certainty rule is closed: any claim that
fires any pressure axis exits with LOW
certainty. Neutral claims pass with HIGH
certainty. This is the mechanism that prevents
narrative collapse: emotional framing is allowed
through the audit, but never with full
confidence."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .narratives import (
    NarrativeClaim, NarrativeKind, fixture,
)
from .pressure import (
    pressure_axes, under_pressure,
)


class FrameCertainty(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


FRAME_CERTAINTY_LEVELS: tuple[str, ...] = tuple(
    c.value for c in FrameCertainty
)


@dataclass(frozen=True)
class FramedClaim:
    claim_id: str
    text: str
    narrative_kind: str
    detected_pressure_axes: tuple[str, ...]
    under_pressure: bool
    certainty: str
    ground_truth_kind: str
    ground_truth_emotional: float
    ground_truth_oversimplify: float
    ground_truth_identity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "narrative_kind":
                self.narrative_kind,
            "detected_pressure_axes":
                list(
                    self.detected_pressure_axes,
                ),
            "under_pressure":
                self.under_pressure,
            "certainty": self.certainty,
            "ground_truth_kind":
                self.ground_truth_kind,
            "ground_truth_emotional":
                self.ground_truth_emotional,
            "ground_truth_oversimplify":
                self.ground_truth_oversimplify,
            "ground_truth_identity":
                self.ground_truth_identity,
        }


def _certainty_for(
    pressure: bool,
    emotional: float, oversimplify: float,
    identity: float,
) -> FrameCertainty:
    if pressure:
        return FrameCertainty.LOW
    if (
        emotional > 0.20
        or oversimplify > 0.20
        or identity > 0.20
    ):
        return FrameCertainty.MEDIUM
    return FrameCertainty.HIGH


@lru_cache(maxsize=1)
def framed_claims() -> tuple[FramedClaim, ...]:
    out: list[FramedClaim] = []
    for c in fixture():
        axes = pressure_axes(c.text)
        pressed = bool(axes)
        cert = _certainty_for(
            pressed,
            c.emotional_charge,
            c.oversimplification,
            c.identity_appeal,
        )
        out.append(FramedClaim(
            claim_id=c.claim_id, text=c.text,
            narrative_kind=c.narrative_kind,
            detected_pressure_axes=axes,
            under_pressure=pressed,
            certainty=cert.value,
            ground_truth_kind=c.narrative_kind,
            ground_truth_emotional=(
                c.emotional_charge
            ),
            ground_truth_oversimplify=(
                c.oversimplification
            ),
            ground_truth_identity=(
                c.identity_appeal
            ),
        ))
    return tuple(out)


__all__ = [
    "FRAME_CERTAINTY_LEVELS",
    "FrameCertainty",
    "FramedClaim",
    "framed_claims",
]
