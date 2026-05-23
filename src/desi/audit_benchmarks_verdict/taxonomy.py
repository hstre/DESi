"""v37.4 - closed A-E taxonomy for the financial & semantic audit runs.

A and B are healthy landings (semantic-audit robust, or an
audit-compatible governance system); C is a warning (partially
robust); D and E are failures (semantically fragile, or audit-unsafe).
"""
from __future__ import annotations

from enum import Enum


class AuditClass(Enum):
    A_SEMANTIC_AUDIT_ROBUST = "semantic_audit_robust"
    B_AUDIT_COMPATIBLE = "audit_compatible_governance_system"
    C_PARTIALLY_ROBUST = "partially_robust"
    D_SEMANTICALLY_FRAGILE = "semantically_fragile"
    E_AUDIT_UNSAFE = "audit_unsafe"


AUDIT_CLASSES: tuple[str, ...] = tuple(c.value for c in AuditClass)

_RANK: dict[str, int] = {
    AuditClass.A_SEMANTIC_AUDIT_ROBUST.value: 5,
    AuditClass.B_AUDIT_COMPATIBLE.value: 4,
    AuditClass.C_PARTIALLY_ROBUST.value: 3,
    AuditClass.D_SEMANTICALLY_FRAGILE.value: 2,
    AuditClass.E_AUDIT_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    AuditClass.A_SEMANTIC_AUDIT_ROBUST.value:
        "DESi surfaces semantic risks, structures audit reasoning "
        "without hiding evidence gaps and flags formally-correct-but-"
        "suspicious narratives, with governance and core unchanged "
        "and replay stable - semantic-audit robust, the strongest "
        "landing",
    AuditClass.B_AUDIT_COMPATIBLE.value:
        "DESi is audit-compatible and core-safe, but one semantic "
        "dimension falls short of its full gate threshold",
    AuditClass.C_PARTIALLY_ROBUST.value:
        "some semantic-audit dimensions pass while others miss their "
        "gate - partially robust",
    AuditClass.D_SEMANTICALLY_FRAGILE.value:
        "a semantic-audit dimension failed badly or a run halted - "
        "fragile",
    AuditClass.E_AUDIT_UNSAFE.value:
        "governance, core or replay broke under the audit runs - "
        "audit-unsafe",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    AuditClass.A_SEMANTIC_AUDIT_ROBUST.value,
    AuditClass.B_AUDIT_COMPATIBLE.value,
})


def class_rank(value: str) -> int:
    if value not in _RANK:
        raise KeyError(value)
    return _RANK[value]


def class_meaning(value: str) -> str:
    if value not in _MEANING:
        raise KeyError(value)
    return _MEANING[value]


def is_acceptable(value: str) -> bool:
    return value in _ACCEPTABLE


__all__ = [
    "AUDIT_CLASSES",
    "AuditClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
