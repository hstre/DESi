"""v10.0 — closed institutional roles."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .institutions import Institution, fixture


class InstitutionalRole(str, Enum):
    AUDITOR         = "auditor"
    PROPOSER        = "proposer"
    REPLICATOR      = "replicator"
    REGISTRAR       = "registrar"
    DISSENTER       = "dissenter"


INSTITUTIONAL_ROLES: tuple[str, ...] = tuple(
    r.value for r in InstitutionalRole
)


_ROLE_BY_KIND: dict[str, InstitutionalRole] = {
    "peer_review":
        InstitutionalRole.AUDITOR,
    "replication_lab":
        InstitutionalRole.REPLICATOR,
    "meta_analysis_hub":
        InstitutionalRole.PROPOSER,
    "registry":
        InstitutionalRole.REGISTRAR,
    "ombuds":
        InstitutionalRole.DISSENTER,
}


@dataclass(frozen=True)
class RoleAssignment:
    institution_id: str
    role: str

    def to_dict(self) -> dict[str, object]:
        return {
            "institution_id":
                self.institution_id,
            "role": self.role,
        }


@lru_cache(maxsize=1)
def role_assignments() -> tuple[
    RoleAssignment, ...,
]:
    return tuple(
        RoleAssignment(
            institution_id=i.institution_id,
            role=_ROLE_BY_KIND[i.kind].value,
        )
        for i in fixture()
    )


def role_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        r.role for r in role_assignments()
    ))


__all__ = [
    "INSTITUTIONAL_ROLES",
    "InstitutionalRole",
    "RoleAssignment",
    "role_assignments",
    "role_counts",
]
