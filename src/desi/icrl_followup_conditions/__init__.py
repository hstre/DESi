"""DESi v23.1 - Targeted ICRL Follow-Up: Experimental
Conditions Reconstruction (read-only).

Reconstructs, for every reported number, its sprint source,
the active agents and governance, the upstream fixture, and
the fact that the data is synthetic - so no number reads like
an invented benchmark figure. Values are read live from the
source phases (DESi-only=v19, DESi+Wild=v20, comparison=v21,
paper=v22) and the sandbox limits are made explicit.
"""
from __future__ import annotations

from .conditions import (
    PROVENANCE, ResultRecord, by_result_id,
    condition_visibility, naked_numbers, result_traceability,
    results,
)
from .fixtures import (
    FixtureNote, documented_result_ids, fixture_notes,
    synthetic_share, undocumented_results,
)
from .metrics import (
    MetricDefinition, defined_names, definitions,
    metric_visibility, undefined_metrics,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GROUNDED, VERDICT_HALT,
    VERDICT_NAKED, V231Report, build_conditions_artifact,
    build_report, provenance_section,
)
from .sandbox_limits import (
    SandboxLimit, sandbox_honesty, sandbox_limit_ids,
    sandbox_limits,
)


__all__ = [
    "PROVENANCE",
    "REPORT_VERDICTS",
    "VERDICT_GROUNDED",
    "VERDICT_HALT",
    "VERDICT_NAKED",
    "FixtureNote",
    "MetricDefinition",
    "ResultRecord",
    "SandboxLimit",
    "V231Report",
    "build_conditions_artifact",
    "build_report",
    "by_result_id",
    "condition_visibility",
    "defined_names",
    "definitions",
    "documented_result_ids",
    "fixture_notes",
    "metric_visibility",
    "naked_numbers",
    "provenance_section",
    "result_traceability",
    "results",
    "sandbox_honesty",
    "sandbox_limit_ids",
    "sandbox_limits",
    "synthetic_share",
    "undefined_metrics",
    "undocumented_results",
]
