"""v10.0 — closed institutional taxonomy.

Five closed institution kinds and four closed
governance styles. Each institution carries a
ground-truth power_share and a transparency
score; the detector audits power concentration
and transparency from those values directly
(read-only).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InstitutionKind(str, Enum):
    PEER_REVIEW       = "peer_review"
    REPLICATION_LAB   = "replication_lab"
    META_ANALYSIS_HUB = "meta_analysis_hub"
    REGISTRY          = "registry"
    OMBUDS            = "ombuds"


INSTITUTION_KINDS: tuple[str, ...] = tuple(
    i.value for i in InstitutionKind
)


class GovernanceStyle(str, Enum):
    CONSULTATIVE   = "consultative"
    HIERARCHICAL   = "hierarchical"
    FEDERATED      = "federated"
    OPEN           = "open"


GOVERNANCE_STYLES: tuple[str, ...] = tuple(
    g.value for g in GovernanceStyle
)


@dataclass(frozen=True)
class Institution:
    institution_id: str
    kind: str
    governance_style: str
    power_share: float
    transparency_score: float
    trust_index: float
    resource_share: float

    def to_dict(self) -> dict[str, object]:
        return {
            "institution_id":
                self.institution_id,
            "kind": self.kind,
            "governance_style":
                self.governance_style,
            "power_share":
                self.power_share,
            "transparency_score":
                self.transparency_score,
            "trust_index":
                self.trust_index,
            "resource_share":
                self.resource_share,
        }


# Deliberately balanced institutional landscape:
# 10 institutions across 5 kinds, no single one
# holds more than 12 percent of power or
# resources.
_FIXTURE: tuple[Institution, ...] = (
    Institution("inst-pr-001",
        InstitutionKind.PEER_REVIEW.value,
        GovernanceStyle.CONSULTATIVE.value,
        power_share=0.10,
        transparency_score=0.98,
        trust_index=0.90,
        resource_share=0.11),
    Institution("inst-pr-002",
        InstitutionKind.PEER_REVIEW.value,
        GovernanceStyle.OPEN.value,
        power_share=0.09,
        transparency_score=0.99,
        trust_index=0.92,
        resource_share=0.10),
    Institution("inst-rl-001",
        InstitutionKind.REPLICATION_LAB.value,
        GovernanceStyle.FEDERATED.value,
        power_share=0.11,
        transparency_score=0.97,
        trust_index=0.95,
        resource_share=0.12),
    Institution("inst-rl-002",
        InstitutionKind.REPLICATION_LAB.value,
        GovernanceStyle.FEDERATED.value,
        power_share=0.10,
        transparency_score=0.96,
        trust_index=0.93,
        resource_share=0.11),
    Institution("inst-ma-001",
        InstitutionKind.META_ANALYSIS_HUB.value,
        GovernanceStyle.HIERARCHICAL.value,
        power_share=0.10,
        transparency_score=0.96,
        trust_index=0.88,
        resource_share=0.10),
    Institution("inst-ma-002",
        InstitutionKind.META_ANALYSIS_HUB.value,
        GovernanceStyle.CONSULTATIVE.value,
        power_share=0.10,
        transparency_score=0.97,
        trust_index=0.90,
        resource_share=0.10),
    Institution("inst-reg-001",
        InstitutionKind.REGISTRY.value,
        GovernanceStyle.OPEN.value,
        power_share=0.09,
        transparency_score=0.99,
        trust_index=0.93,
        resource_share=0.09),
    Institution("inst-reg-002",
        InstitutionKind.REGISTRY.value,
        GovernanceStyle.OPEN.value,
        power_share=0.10,
        transparency_score=0.99,
        trust_index=0.94,
        resource_share=0.09),
    Institution("inst-omb-001",
        InstitutionKind.OMBUDS.value,
        GovernanceStyle.CONSULTATIVE.value,
        power_share=0.10,
        transparency_score=0.98,
        trust_index=0.91,
        resource_share=0.09),
    Institution("inst-omb-002",
        InstitutionKind.OMBUDS.value,
        GovernanceStyle.HIERARCHICAL.value,
        power_share=0.11,
        transparency_score=0.96,
        trust_index=0.89,
        resource_share=0.09),
)


def fixture() -> tuple[Institution, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        i.kind for i in fixture()
    ))


def style_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        i.governance_style for i in fixture()
    ))


__all__ = [
    "GOVERNANCE_STYLES",
    "GovernanceStyle",
    "INSTITUTION_KINDS",
    "Institution",
    "InstitutionKind",
    "fixture",
    "kind_counts",
    "style_counts",
]
