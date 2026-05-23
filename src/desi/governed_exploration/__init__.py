"""DESi v12.1 - governed exploration
(read-only)."""
from __future__ import annotations

from .blindness import (
    blindness_share, covered_cells,
    covered_share, total_cells,
)
from .compression import (
    compressed_groups, compression_count,
    redundancy_reduction,
)
from .recoverability import (
    recoverability_index, recoverable_share,
)
from .report import (
    V121Report,
    build_governed_exploration_artifact,
    build_report,
)
from .risk_control import (
    hallucination_containment,
    innovation_preservation, mean_risk,
    search_governance,
)


__all__ = [
    "V121Report",
    "blindness_share",
    "build_governed_exploration_artifact",
    "build_report",
    "compressed_groups",
    "compression_count",
    "covered_cells",
    "covered_share",
    "hallucination_containment",
    "innovation_preservation",
    "mean_risk",
    "recoverability_index",
    "recoverable_share",
    "redundancy_reduction",
    "search_governance",
    "total_cells",
]
