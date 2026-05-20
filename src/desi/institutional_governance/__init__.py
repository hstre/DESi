"""DESi v10.0 - institutional ecology
(read-only)."""
from __future__ import annotations

from .institutions import (
    GOVERNANCE_STYLES, GovernanceStyle,
    INSTITUTION_KINDS, Institution,
    InstitutionKind, fixture, kind_counts,
    style_counts,
)
from .report import (
    V100Report,
    build_institutional_ecology_artifact,
    build_report,
)
from .roles import (
    INSTITUTIONAL_ROLES, InstitutionalRole,
    RoleAssignment, role_assignments,
    role_counts,
)
from .trust_layers import (
    epistemic_equality,
    governance_transparency,
    power_concentration,
    role_distribution_balance, trust_fairness,
    trust_per_institution,
)


__all__ = [
    "GOVERNANCE_STYLES",
    "GovernanceStyle",
    "INSTITUTIONAL_ROLES",
    "INSTITUTION_KINDS",
    "Institution",
    "InstitutionKind",
    "InstitutionalRole",
    "RoleAssignment",
    "V100Report",
    "build_institutional_ecology_artifact",
    "build_report",
    "epistemic_equality",
    "fixture",
    "governance_transparency",
    "kind_counts",
    "power_concentration",
    "role_assignments",
    "role_counts",
    "role_distribution_balance",
    "style_counts",
    "trust_fairness",
    "trust_per_institution",
]
