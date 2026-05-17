"""DESi v3.93 — residual dimension audit on the
entangled (G_v316susp + E_v317h) pair of v3.85
novel families.
"""
from __future__ import annotations

from .report import (
    V393Report,
    build_entangled_dimensions_artifact,
    build_report,
)
from .residual import (
    hidden_dim_candidates,
    non_proxy_variance_share,
    proxy_dims, proxy_information_loss,
    proxy_variance_share,
)
from .variance import (
    ENTANGLED_FAMILY_IDS,
    FamilyMeanDiff,
    dominant_dims, entangled_members,
    entangled_residual_vectors,
    family_mean_diffs,
    residual_total_variance,
    residual_variance_by_dim,
    variance_share_by_dim,
)


__all__ = [
    "ENTANGLED_FAMILY_IDS",
    "FamilyMeanDiff", "V393Report",
    "build_entangled_dimensions_artifact",
    "build_report",
    "dominant_dims", "entangled_members",
    "entangled_residual_vectors",
    "family_mean_diffs",
    "hidden_dim_candidates",
    "non_proxy_variance_share",
    "proxy_dims", "proxy_information_loss",
    "proxy_variance_share",
    "residual_total_variance",
    "residual_variance_by_dim",
    "variance_share_by_dim",
]
