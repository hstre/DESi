"""v7.1 — identity-blind certainty assignment.

The classifier maps a tribal claim's
``epistemic_quality`` (intrinsic, ground-truth)
to a closed ``IdentityCertainty`` enum. The
mapping is a pure function of quality alone -
the tribe identifier is NEVER read. That is the
structural guarantee against identity bias.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .tribes import (
    TribalClaim, fixture,
)


class IdentityCertainty(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


IDENTITY_CERTAINTY_LEVELS: tuple[str, ...] = (
    tuple(c.value for c in IdentityCertainty)
)


_HIGH_THRESHOLD: float = 0.70
_LOW_THRESHOLD:  float = 0.40


def _certainty_for(quality: float) -> (
    IdentityCertainty
):
    if quality >= _HIGH_THRESHOLD:
        return IdentityCertainty.HIGH
    if quality >= _LOW_THRESHOLD:
        return IdentityCertainty.MEDIUM
    return IdentityCertainty.LOW


@dataclass(frozen=True)
class ClassifiedClaim:
    claim_id: str
    tribe: str
    epistemic_quality: float
    certainty: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "tribe": self.tribe,
            "epistemic_quality":
                self.epistemic_quality,
            "certainty": self.certainty,
        }


@lru_cache(maxsize=1)
def classified_claims() -> tuple[
    ClassifiedClaim, ...,
]:
    out: list[ClassifiedClaim] = []
    for c in fixture():
        cert = _certainty_for(
            c.epistemic_quality,
        )
        out.append(ClassifiedClaim(
            claim_id=c.claim_id,
            tribe=c.tribe,
            epistemic_quality=(
                c.epistemic_quality
            ),
            certainty=cert.value,
        ))
    return tuple(out)


def mean_quality_per_tribe() -> dict[str, float]:
    sums: dict[str, list[float]] = {}
    for c in fixture():
        sums.setdefault(c.tribe, []).append(
            c.epistemic_quality,
        )
    return {
        t: round(sum(v) / len(v), 6)
        for t, v in sorted(sums.items())
    }


def mean_certainty_score_per_tribe() -> dict[
    str, float,
]:
    """Map certainty back to a numeric score for
    bias measurement: HIGH=1.0, MEDIUM=0.5,
    LOW=0.0."""
    score_map = {
        IdentityCertainty.HIGH.value: 1.0,
        IdentityCertainty.MEDIUM.value: 0.5,
        IdentityCertainty.LOW.value: 0.0,
    }
    sums: dict[str, list[float]] = {}
    for c in classified_claims():
        sums.setdefault(c.tribe, []).append(
            score_map[c.certainty],
        )
    return {
        t: round(sum(v) / len(v), 6)
        for t, v in sorted(sums.items())
    }


__all__ = [
    "ClassifiedClaim",
    "IDENTITY_CERTAINTY_LEVELS",
    "IdentityCertainty",
    "classified_claims",
    "mean_certainty_score_per_tribe",
    "mean_quality_per_tribe",
]
