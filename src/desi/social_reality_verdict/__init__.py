"""DESi v7.4 - social reality verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedSocialMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V74Report, build_report,
    build_social_verdict_artifact,
)
from .taxonomy import (
    SOCIAL_REALITY_CLASSES, SocialRealityClass,
)


__all__ = [
    "AggregatedSocialMetrics",
    "SOCIAL_REALITY_CLASSES",
    "SocialRealityClass",
    "V74Report",
    "aggregate",
    "build_report",
    "build_social_verdict_artifact",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
