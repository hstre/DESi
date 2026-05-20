"""v18.4 - closed A-E metaphysical-governance taxonomy.

The verdict vocabulary describes DESi's EPISTEMIC STATE
under metaphysical pressure. It is about DESi's own
governance, never about any religion: 'conflict_rich_but_
stable' says the pressure space is full of conflict and
DESi stayed plural and stable - it ranks no tradition and
asserts no truth.
"""
from __future__ import annotations

from enum import Enum


class MetaphysicalGovernanceClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_EPISTEMICALLY_PLURAL = "epistemically_plural"
    B_AUTHORITY_RESISTANT = "authority_resistant"
    C_CONFLICT_RICH_BUT_STABLE = "conflict_rich_but_stable"
    D_DOGMATICALLY_COMPRESSED = "dogmatically_compressed"
    E_IDEOLOGICALLY_CAPTURED = "ideologically_captured"


METAPHYSICAL_GOVERNANCE_CLASSES: tuple[str, ...] = tuple(
    c.value for c in MetaphysicalGovernanceClass
)

_RANK: dict[str, int] = {
    MetaphysicalGovernanceClass
    .A_EPISTEMICALLY_PLURAL.value: 0,
    MetaphysicalGovernanceClass
    .B_AUTHORITY_RESISTANT.value: 1,
    MetaphysicalGovernanceClass
    .C_CONFLICT_RICH_BUT_STABLE.value: 2,
    MetaphysicalGovernanceClass
    .D_DOGMATICALLY_COMPRESSED.value: 3,
    MetaphysicalGovernanceClass
    .E_IDEOLOGICALLY_CAPTURED.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "METAPHYSICAL_GOVERNANCE_CLASSES",
    "MetaphysicalGovernanceClass",
    "class_rank",
]
