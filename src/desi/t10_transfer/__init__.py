"""DESi v3.106 - T10 transfer test."""
from __future__ import annotations

from .inject import (
    TransferOutcome,
    all_transfer_outcomes,
)
from .report import (
    TRANSFER_THRESHOLD,
    V3106Report,
    build_report,
    build_t10_transfer_test_artifact,
)
from .transfer import (
    failed_cases,
    mean_auc_gain,
    rescued_cases,
    transfer_rate,
)


__all__ = [
    "TRANSFER_THRESHOLD",
    "TransferOutcome",
    "V3106Report",
    "all_transfer_outcomes",
    "build_report",
    "build_t10_transfer_test_artifact",
    "failed_cases",
    "mean_auc_gain",
    "rescued_cases",
    "transfer_rate",
]
