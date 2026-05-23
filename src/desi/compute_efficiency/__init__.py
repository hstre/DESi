"""DESi v11.3 - compute efficiency audit
(read-only)."""
from __future__ import annotations

from .compression import (
    per_position_compression,
)
from .costs import (
    baseline_energy, baseline_time_ms,
    guided_energy, guided_time_ms,
)
from .efficiency import (
    branch_compression, compute_reduction,
    elo_delta_proxy, quality_preservation,
)
from .report import (
    V113Report, build_efficiency_artifact,
    build_report,
)


__all__ = [
    "V113Report",
    "baseline_energy",
    "baseline_time_ms",
    "branch_compression",
    "build_efficiency_artifact",
    "build_report",
    "compute_reduction",
    "elo_delta_proxy",
    "guided_energy",
    "guided_time_ms",
    "per_position_compression",
    "quality_preservation",
]
