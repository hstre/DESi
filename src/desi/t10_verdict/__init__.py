"""DESi v3.112 - T10 proxy verdict."""
from __future__ import annotations

from .report import (
    VALIDATED_VOCAB_MIN,
    V3112Report,
    build_report,
    build_t10_proxy_verdict_artifact,
)
from .verdict import (
    DimClassification,
    DimVerdict,
    SMALL_VOCAB_DIMS,
    all_classifications,
    ambiguous_dims,
    classify,
    epistemic_dims,
    proxy_dims,
    validated_vocab_size,
)


__all__ = [
    "DimClassification",
    "DimVerdict",
    "SMALL_VOCAB_DIMS",
    "VALIDATED_VOCAB_MIN",
    "V3112Report",
    "all_classifications",
    "ambiguous_dims",
    "build_report",
    "build_t10_proxy_verdict_artifact",
    "classify",
    "epistemic_dims",
    "proxy_dims",
    "validated_vocab_size",
]
