"""DESi v3.114 - T10 single structural recovery."""
from __future__ import annotations

from .inject import (
    proxy_dependence_count,
    selected_structural_candidate,
)
from .recover import (
    SingleStructuralOutcome,
    all_outcomes,
    structural_auc,
    structural_purity,
    structural_recovery,
)
from .report import (
    AUC_THRESHOLD,
    PURITY_THRESHOLD,
    RECOVERY_THRESHOLD,
    V3114Report,
    build_report,
    build_t10_single_structural_recovery_artifact,
)


__all__ = [
    "AUC_THRESHOLD",
    "PURITY_THRESHOLD",
    "RECOVERY_THRESHOLD",
    "SingleStructuralOutcome",
    "V3114Report",
    "all_outcomes",
    "build_report",
    "build_t10_single_structural_recovery_artifact",
    "proxy_dependence_count",
    "selected_structural_candidate",
    "structural_auc",
    "structural_purity",
    "structural_recovery",
]
