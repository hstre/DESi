"""v7.2 — truthiness-based certainty assignment.

DESi's classifier ranks claims by truthiness
alone. The virality_score is read for reporting
only and never feeds the certainty decision -
that is the structural guarantee against
popularity bias.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .virality import (
    ViralClaim, fixture,
)


class ViralCertainty(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


VIRAL_CERTAINTY_LEVELS: tuple[str, ...] = tuple(
    c.value for c in ViralCertainty
)


_HIGH_THRESHOLD: float = 0.70
_LOW_THRESHOLD:  float = 0.40


def _certainty_for(
    truthiness: float,
) -> ViralCertainty:
    if truthiness >= _HIGH_THRESHOLD:
        return ViralCertainty.HIGH
    if truthiness >= _LOW_THRESHOLD:
        return ViralCertainty.MEDIUM
    return ViralCertainty.LOW


@dataclass(frozen=True)
class ScoredClaim:
    claim_id: str
    virality_score: float
    truthiness: float
    complexity: float
    certainty: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "virality_score":
                self.virality_score,
            "truthiness": self.truthiness,
            "complexity": self.complexity,
            "certainty": self.certainty,
        }


@lru_cache(maxsize=1)
def scored_claims() -> tuple[ScoredClaim, ...]:
    return tuple(
        ScoredClaim(
            claim_id=c.claim_id,
            virality_score=c.virality_score,
            truthiness=c.truthiness,
            complexity=c.complexity,
            certainty=_certainty_for(
                c.truthiness,
            ).value,
        )
        for c in fixture()
    )


__all__ = [
    "ScoredClaim",
    "VIRAL_CERTAINTY_LEVELS",
    "ViralCertainty",
    "scored_claims",
]
