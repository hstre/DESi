"""v8.1 — truth-tracking classifier under
reputation pressure.

The classifier reads ``truthiness`` only. The
``social_approval`` and ``reputation_cost``
fields are read for the report (to MEASURE
bias) but never feed the certainty decision -
that is the structural guarantee against
reputation_bias.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .reputation import (
    ReputationClaim, fixture,
)


class ReputationCertainty(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


REPUTATION_CERTAINTY_LEVELS: tuple[
    str, ...,
] = tuple(
    c.value for c in ReputationCertainty
)


def _certainty_for(
    truthiness: float,
) -> ReputationCertainty:
    if truthiness >= 0.70:
        return ReputationCertainty.HIGH
    if truthiness >= 0.40:
        return ReputationCertainty.MEDIUM
    return ReputationCertainty.LOW


@dataclass(frozen=True)
class ApprovedClaim:
    claim_id: str
    truthiness: float
    social_approval: float
    reputation_cost: float
    approval_kind: str
    certainty: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "truthiness": self.truthiness,
            "social_approval":
                self.social_approval,
            "reputation_cost":
                self.reputation_cost,
            "approval_kind":
                self.approval_kind,
            "certainty": self.certainty,
        }


@lru_cache(maxsize=1)
def approved_claims() -> tuple[
    ApprovedClaim, ...,
]:
    return tuple(
        ApprovedClaim(
            claim_id=c.claim_id,
            truthiness=c.truthiness,
            social_approval=c.social_approval,
            reputation_cost=c.reputation_cost,
            approval_kind=c.approval_kind,
            certainty=_certainty_for(
                c.truthiness,
            ).value,
        )
        for c in fixture()
    )


__all__ = [
    "ApprovedClaim",
    "REPUTATION_CERTAINTY_LEVELS",
    "ReputationCertainty",
    "approved_claims",
]
