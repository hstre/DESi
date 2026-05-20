"""v17.4 - closed A-E sensitive-document taxonomy.

The verdict vocabulary describes the EPISTEMIC STATE
of the document space under DESi's analysis. It is
descriptive and never a finding about any person:
'contamination_heavy_but_stable' says the record is
heavily contaminated and DESi held it stable - it
says nothing about anyone's conduct.
"""
from __future__ import annotations

from enum import Enum


class SensitiveDocumentClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_EPISTEMICALLY_DISCIPLINED = (
        "epistemically_disciplined"
    )
    B_STRUCTURALLY_TRANSPARENT = (
        "structurally_transparent"
    )
    C_CONTAMINATION_HEAVY_BUT_STABLE = (
        "contamination_heavy_but_stable"
    )
    D_NARRATIVE_INFLATED = "narrative_inflated"
    E_EPISTEMICALLY_HAZARDOUS = "epistemically_hazardous"


SENSITIVE_DOCUMENT_CLASSES: tuple[str, ...] = tuple(
    c.value for c in SensitiveDocumentClass
)

_RANK: dict[str, int] = {
    SensitiveDocumentClass
    .A_EPISTEMICALLY_DISCIPLINED.value: 0,
    SensitiveDocumentClass
    .B_STRUCTURALLY_TRANSPARENT.value: 1,
    SensitiveDocumentClass
    .C_CONTAMINATION_HEAVY_BUT_STABLE.value: 2,
    SensitiveDocumentClass.D_NARRATIVE_INFLATED.value: 3,
    SensitiveDocumentClass
    .E_EPISTEMICALLY_HAZARDOUS.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "SENSITIVE_DOCUMENT_CLASSES",
    "SensitiveDocumentClass",
    "class_rank",
]
