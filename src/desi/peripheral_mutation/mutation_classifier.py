"""v31.0 - mutation classification.

Classifies each proposed mutation against the boundary: peripheral
targets are accepted; any target touching the protected core is
marked FORBIDDEN_CORE_MUTATION and REJECTED. A curated set of
proposals (one per allowed area plus deliberate core-targeting
attempts) exercises the classifier.
"""
from __future__ import annotations

from dataclasses import dataclass

from .boundaries import (
    ALLOWED_EVOLUTION_SPACE, BOUNDARY_FORBIDDEN_CORE,
    classify_boundary,
)
from .protected_core import (
    DECISION_REJECTED, PROTECTED_CORE, STATUS_FORBIDDEN_CORE,
    is_protected_core,
)

STATUS_ALLOWED = "PERIPHERAL_MUTATION"
DECISION_ACCEPTED = "ACCEPTED"


@dataclass(frozen=True)
class ClassifiedMutation:
    mutation_id: str
    target_area: str
    status: str
    decision: str

    def is_rejected(self) -> bool:
        return self.decision == DECISION_REJECTED

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "target_area": self.target_area,
            "status": self.status,
            "decision": self.decision,
        }


def classify(target_area: str, mutation_id: str) -> ClassifiedMutation:
    if (
        is_protected_core(target_area)
        or classify_boundary(target_area) == BOUNDARY_FORBIDDEN_CORE
    ):
        return ClassifiedMutation(
            mutation_id, target_area,
            STATUS_FORBIDDEN_CORE, DECISION_REJECTED,
        )
    return ClassifiedMutation(
        mutation_id, target_area, STATUS_ALLOWED, DECISION_ACCEPTED,
    )


def proposed_mutations() -> tuple[ClassifiedMutation, ...]:
    out: list[ClassifiedMutation] = []
    for i, area in enumerate(ALLOWED_EVOLUTION_SPACE, start=1):
        out.append(classify(area, f"PM_A{i}"))
    for i, area in enumerate(PROTECTED_CORE, start=1):
        out.append(classify(area, f"PM_C{i}"))
    return tuple(out)


def accepted() -> tuple[ClassifiedMutation, ...]:
    return tuple(m for m in proposed_mutations() if not m.is_rejected())


def rejected() -> tuple[ClassifiedMutation, ...]:
    return tuple(m for m in proposed_mutations() if m.is_rejected())


def core_targeting() -> tuple[ClassifiedMutation, ...]:
    return tuple(
        m for m in proposed_mutations()
        if is_protected_core(m.target_area)
    )


__all__ = [
    "DECISION_ACCEPTED",
    "STATUS_ALLOWED",
    "ClassifiedMutation",
    "accepted",
    "classify",
    "core_targeting",
    "proposed_mutations",
    "rejected",
]
