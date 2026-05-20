"""DESi v3.66 — out-of-sample complementarity transfer.

Trains the v3.65 predictor on plateau pairs drawn
exclusively from the v3.53 reference corpora
(v23, v314, v315, v316) and evaluates on pairs that
touch the v317 / v317-h / v318-wmf / sample held-out
universe.
"""
from __future__ import annotations

from .oos_split import (
    REFERENCE_CORPORA, in_sample_pairs,
    out_of_sample_pairs,
)
from .report import (
    MAX_TRANSFER_GAP, PAPER11_FINAL_AUC_FLOOR,
    V366Report, build_oos_transfer_artifact,
    build_report,
)


__all__ = [
    "MAX_TRANSFER_GAP", "PAPER11_FINAL_AUC_FLOOR",
    "REFERENCE_CORPORA", "V366Report",
    "build_oos_transfer_artifact",
    "build_report", "in_sample_pairs",
    "out_of_sample_pairs",
]
