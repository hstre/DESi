"""DESi v3.104 - T10 recovery vs complexity audit."""
from __future__ import annotations

from .complexity import (
    compression_delta,
    overfitting_risk,
    state_dim_cost,
    tail_vector_cost,
)
from .report import (
    V3104Report,
    build_report,
    build_t10_recovery_vs_complexity_artifact,
)
from .tradeoff import (
    architecture_roi,
    complexity_cost,
    recovery_gain,
)


__all__ = [
    "V3104Report",
    "architecture_roi",
    "build_report",
    "build_t10_recovery_vs_complexity_artifact",
    "complexity_cost",
    "compression_delta",
    "overfitting_risk",
    "recovery_gain",
    "state_dim_cost",
    "tail_vector_cost",
]
