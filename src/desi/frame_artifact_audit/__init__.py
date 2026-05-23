"""DESi v3.49 — frame artifact audit.

Probes whether the v3.44 radius-bounded selector's
phase transition is a genuine geometric separation
or a frame_id proxy. Five closed masks zero out or
permute the frame dimension and rerun the radius
sweep; the report records how each mask affects the
step function.
"""
from __future__ import annotations

from .ablation import (
    MaskedOutcome, run_all_combinations, run_under_mask,
)
from .mask import (
    MaskKind, apply_mask, build_permutation_table,
)
from .report import (
    MaskResult, V349Report,
    build_frame_artifact_audit_artifact, build_report,
)


__all__ = [
    "MaskKind", "MaskResult", "MaskedOutcome",
    "V349Report", "apply_mask",
    "build_frame_artifact_audit_artifact",
    "build_permutation_table", "build_report",
    "run_all_combinations", "run_under_mask",
]
