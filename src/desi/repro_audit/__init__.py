"""DESi v4.11 — Reproducibility Hardening Audit.

Read-only audit module that:

* fingerprints the current Python / dependency
  environment,
* builds a global replay matrix across every pinned
  version (v2.8, v3.11-v3.23, v4.0-v4.10),
* classifies each entry into a closed
  ``ReproducibilityClass``,
* declares an explicit ``tool_repro_policy`` for the
  SymPy-dependent v1.9 tool benchmark,
* assembles a v4.11 report + writes the environment +
  replay matrix to ``artifacts/v4_11/``.
"""
from __future__ import annotations

from .enums import (
    RecommendationOutcome, ReproducibilityClass,
    ToolReproPolicy,
)
from .environment import EnvironmentFingerprint, fingerprint
from .negative_controls import (
    ReproNC, all_repro_ncs, classification_accuracy,
    classify_nc,
)
from .replay_matrix import (
    MatrixEntry, build_entry, build_matrix,
)
from .report import (
    MIN_CLASSIFICATION_ACCURACY, MIN_NC_COUNT,
    NCOutcome, V2_8_FROZEN_FAILCASE_HASH,
    V2_8_FROZEN_RECONSTRUCTION_HASH, V411Report,
    build_v411_report,
)
from .tool_policy import (
    TOOL_REPRO_POLICY, expected_correct_count,
    expected_symbolic_outcome,
)


__all__ = [
    "EnvironmentFingerprint", "MIN_CLASSIFICATION_ACCURACY",
    "MIN_NC_COUNT", "MatrixEntry", "NCOutcome",
    "RecommendationOutcome", "ReproNC",
    "ReproducibilityClass", "TOOL_REPRO_POLICY",
    "ToolReproPolicy", "V2_8_FROZEN_FAILCASE_HASH",
    "V2_8_FROZEN_RECONSTRUCTION_HASH", "V411Report",
    "all_repro_ncs", "build_entry", "build_matrix",
    "build_v411_report", "classification_accuracy",
    "classify_nc", "expected_correct_count",
    "expected_symbolic_outcome", "fingerprint",
]
