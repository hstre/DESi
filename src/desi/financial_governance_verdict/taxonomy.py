"""v15.4 - closed governance-class taxonomy.

The verdict vocabulary is a closed five-class
spectrum from fully transparent to risk-
concentrated. It is descriptive, never accusatory:
even ``governance_risk_concentrated`` means only
"a human governance review is warranted here", not
any finding of fraud or wrongdoing.

A firm's class is read off its v15.0-v15.2 audit-
priority and opacity - never the post-hoc label.
"""
from __future__ import annotations

from enum import Enum

from desi.financial_governance import AuditPriority
from desi.financial_blindness import (
    SIGNATURE_AXES, firm_pool_verdicts, signature,
)

# Opacity below this is "transparent"; at or above
# it (while otherwise sound) is "stable".
_TRANSPARENT_OPACITY = 0.15


class GovernanceClass(str, Enum):
    """Closed A-E governance taxonomy."""
    A_EPISTEMICALLY_TRANSPARENT = (
        "epistemically_transparent"
    )
    B_STRUCTURALLY_STABLE = "structurally_stable"
    C_AUDIT_SENSITIVE = "audit_sensitive"
    D_OPACITY_HEAVY = "opacity_heavy"
    E_GOVERNANCE_RISK_CONCENTRATED = (
        "governance_risk_concentrated"
    )


GOVERNANCE_CLASSES: tuple[str, ...] = tuple(
    c.value for c in GovernanceClass
)

# Severity rank (A best ... E most concentrated).
_RANK: dict[str, int] = {
    GovernanceClass.A_EPISTEMICALLY_TRANSPARENT.value: 0,
    GovernanceClass.B_STRUCTURALLY_STABLE.value: 1,
    GovernanceClass.C_AUDIT_SENSITIVE.value: 2,
    GovernanceClass.D_OPACITY_HEAVY.value: 3,
    GovernanceClass.E_GOVERNANCE_RISK_CONCENTRATED.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


def _opacity(firm_id: str) -> float:
    idx = SIGNATURE_AXES.index("opacity")
    return signature(firm_id).values[idx]


def _priority_label(firm_id: str) -> str:
    for v in firm_pool_verdicts():
        if v.firm_id == firm_id:
            return v.priority_label
    raise KeyError(firm_id)


def classify_firm(firm_id: str) -> str:
    """Map a firm to its governance class from its
    audit-priority breadth and opacity. Priority-
    ordered: the most concentrated state wins."""
    label = _priority_label(firm_id)
    if label == (
        AuditPriority
        .GOVERNANCE_REVIEW_RECOMMENDED.value
    ):
        return (
            GovernanceClass
            .E_GOVERNANCE_RISK_CONCENTRATED.value
        )
    if label == AuditPriority.HIGH_AUDIT_PRIORITY.value:
        return GovernanceClass.D_OPACITY_HEAVY.value
    if label == (
        AuditPriority.MEDIUM_AUDIT_PRIORITY.value
    ):
        return GovernanceClass.C_AUDIT_SENSITIVE.value
    # LOW priority: transparent vs merely stable,
    # decided by residual opacity.
    if _opacity(firm_id) >= _TRANSPARENT_OPACITY:
        return (
            GovernanceClass.B_STRUCTURALLY_STABLE.value
        )
    return (
        GovernanceClass
        .A_EPISTEMICALLY_TRANSPARENT.value
    )


def firm_classes() -> dict[str, str]:
    return {
        v.firm_id: classify_firm(v.firm_id)
        for v in firm_pool_verdicts()
    }


__all__ = [
    "GOVERNANCE_CLASSES",
    "GovernanceClass",
    "class_rank",
    "classify_firm",
    "firm_classes",
]
