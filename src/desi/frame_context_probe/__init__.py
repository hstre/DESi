"""DESi v3.8 frame-context-inheritance probe — read-only over v3.5+v3.6+v3.7."""
from __future__ import annotations

from .contamination import (
    ContaminationResult,
    aggregate_contamination,
    probe_all_fixtures,
)
from .extractor import (
    ContextWindow,
    TargetCase,
    extract_entropy_targets,
)
from .false_inheritance import (
    FalseInheritanceCase,
    FalseInheritanceOutcome,
    NEGATIVE_CONTROLS,
    run_false_inheritance,
)
from .inheritance import (
    InheritanceResult,
    InheritanceTrace,
    simulate,
    simulate_all,
    simulate_target,
)
from .report import (
    FalseInheritanceSummary,
    FrameContextProbeReport,
    InheritanceSummary,
    MAX_FALSE_INHERITANCE_RATE,
    MIN_INHERITANCE_ACCURACY,
    build_context_probe_report,
)
from .signals import ContextSignal

__all__ = [
    "ContaminationResult",
    "ContextSignal",
    "ContextWindow",
    "FalseInheritanceCase",
    "FalseInheritanceOutcome",
    "FalseInheritanceSummary",
    "FrameContextProbeReport",
    "InheritanceResult",
    "InheritanceSummary",
    "InheritanceTrace",
    "MAX_FALSE_INHERITANCE_RATE",
    "MIN_INHERITANCE_ACCURACY",
    "NEGATIVE_CONTROLS",
    "TargetCase",
    "aggregate_contamination",
    "build_context_probe_report",
    "extract_entropy_targets",
    "probe_all_fixtures",
    "run_false_inheritance",
    "simulate",
    "simulate_all",
    "simulate_target",
]
