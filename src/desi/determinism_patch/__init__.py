"""DESi v3.96c - deterministic patch.

Applies a sha256-derived stable hash to the only
production-code site (epistemic_trajectory/
extractor.py line 236) that used Python's salted
built-in hash(). Verifies the v3.96a jitter rate
drops to zero.
"""
from __future__ import annotations

from .patch import PATCH, PatchSpec, patch_helper
from .report import (
    V396cReport,
    build_deterministic_patch_artifact,
    build_report,
)
from .verify import (
    ArtifactDiff,
    artifact_diff_count, artifact_diffs,
    jittery_trajectories_post_patch,
    numerical_delta,
    post_patch_jitter_rate,
    regression_breakage,
)


__all__ = [
    "ArtifactDiff",
    "PATCH",
    "PatchSpec",
    "V396cReport",
    "artifact_diff_count",
    "artifact_diffs",
    "build_deterministic_patch_artifact",
    "build_report",
    "jittery_trajectories_post_patch",
    "numerical_delta",
    "patch_helper",
    "post_patch_jitter_rate",
    "regression_breakage",
]
