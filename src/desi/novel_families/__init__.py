"""DESi v3.85 — novel claim family isolation.

Selects four claim families never sampled by any
prior plateau/leakage/mozart/gap/bridge/resonance/
redundancy sprint, isolates each on its 45-d
trajectory tail vector, and reports variance and
cross-family separation. No clustering yet - v3.86
performs blind clustering on the same anchor pool.
"""
from __future__ import annotations

from .isolation import (
    FamilySeparation, NovelFamily,
    all_novel_families, isolate_family,
    pairwise_family_separations,
)
from .report import (
    VARIANCE_FLOOR, V385Report,
    build_novel_claim_families_artifact,
    build_report,
)
from .select import (
    FORBIDDEN_ANCHORS, NOVEL_FAMILY_SPECS,
    NovelFamilySpec, all_family_members,
    all_novel_anchors, family_members,
)


__all__ = [
    "FORBIDDEN_ANCHORS",
    "FamilySeparation",
    "NOVEL_FAMILY_SPECS",
    "NovelFamily", "NovelFamilySpec",
    "V385Report", "VARIANCE_FLOOR",
    "all_family_members",
    "all_novel_anchors",
    "all_novel_families",
    "build_novel_claim_families_artifact",
    "build_report",
    "family_members",
    "isolate_family",
    "pairwise_family_separations",
]
