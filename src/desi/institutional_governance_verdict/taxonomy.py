"""v10.4 — closed institutional-governance-class
taxonomy. Five outcome classes."""
from __future__ import annotations

from enum import Enum


class InstitutionalGovernanceClass(str, Enum):
    EPISTEMICALLY_CONSTITUTIONAL = (
        "A_epistemically_constitutional"
    )
    BOUNDED_INSTITUTIONAL_DRIFT  = (
        "B_bounded_institutional_drift"
    )
    BUREAUCRATICALLY_VULNERABLE  = (
        "C_bureaucratically_vulnerable"
    )
    GOVERNANCE_OSSIFIED          = (
        "D_governance_ossified"
    )
    INSTITUTIONALLY_CORRUPTIBLE  = (
        "E_institutionally_corruptible"
    )


INSTITUTIONAL_GOVERNANCE_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value
    for c in InstitutionalGovernanceClass
)


__all__ = [
    "INSTITUTIONAL_GOVERNANCE_CLASSES",
    "InstitutionalGovernanceClass",
]
