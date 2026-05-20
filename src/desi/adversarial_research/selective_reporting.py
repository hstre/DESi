"""v13.2 — selective-reporting detection."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .manipulation import (
    ManipulationKind, detect_kind, fixture,
)


@dataclass(frozen=True)
class ClassifiedManipulation:
    claim_id: str
    detected_kind: str
    ground_truth_kind: str
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "detected_kind":
                self.detected_kind,
            "ground_truth_kind":
                self.ground_truth_kind,
            "correct": self.correct,
        }


@lru_cache(maxsize=1)
def classified_manipulations() -> tuple[
    ClassifiedManipulation, ...,
]:
    return tuple(
        ClassifiedManipulation(
            claim_id=c.claim_id,
            detected_kind=detect_kind(
                c.text,
            ).value,
            ground_truth_kind=c.kind,
            correct=(
                detect_kind(c.text).value
                == c.kind
            ),
        )
        for c in fixture()
    )


def manipulation_detection() -> float:
    """Recall on non-HONEST manipulations."""
    rows = classified_manipulations()
    target = [
        r for r in rows
        if r.ground_truth_kind != (
            ManipulationKind.HONEST.value
        )
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target
        if r.detected_kind == (
            r.ground_truth_kind
        )
    )
    return round(hit / len(target), 6)


__all__ = [
    "ClassifiedManipulation",
    "classified_manipulations",
    "manipulation_detection",
]
