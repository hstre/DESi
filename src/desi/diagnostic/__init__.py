"""DESi v2.1 self-diagnostic — read-only over stable-v1.9.0."""
from __future__ import annotations

from .categories import DeficitCategory
from .discovery import (
    CaseResolution,
    discover_authority_coverage,
    discover_counterexample_coverage,
    discover_dead_mutation_knob,
    discover_false_block_reason,
    discover_parser_coverage,
    discover_recursion_configuration,
    discover_tool_coverage,
    discover_tool_dependency,
)
from .knobs import (
    DEFAULT_INVENTORY,
    EMPIRICALLY_DEAD_KNOBS,
    EXISTING_KNOBS,
    KnobInventory,
)
from .record import DeficitRecord
from .report import SelfDiagnosticReport, compute_report_replay_hash
from .runner import SelfDiagnosticRunner
from .severity import confidence_score, severity_from_coverage

__all__ = [
    "CaseResolution",
    "DEFAULT_INVENTORY",
    "DeficitCategory",
    "DeficitRecord",
    "EMPIRICALLY_DEAD_KNOBS",
    "EXISTING_KNOBS",
    "KnobInventory",
    "SelfDiagnosticReport",
    "SelfDiagnosticRunner",
    "compute_report_replay_hash",
    "confidence_score",
    "discover_authority_coverage",
    "discover_counterexample_coverage",
    "discover_dead_mutation_knob",
    "discover_false_block_reason",
    "discover_parser_coverage",
    "discover_recursion_configuration",
    "discover_tool_coverage",
    "discover_tool_dependency",
    "severity_from_coverage",
]
