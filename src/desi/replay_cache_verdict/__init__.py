"""DESi v29.2 - Comparative Real Benchmark Verdict (read-only).

The first real, branch-isolated, measured DESi infrastructure
evolution verdict. Compares DESi_current vs DESi_replay_cache_v1
on measured (not projected) numbers, checks the five-condition
Concept Gate, and confirms the cache delivers a real runtime
improvement with byte-identical artifacts, unchanged governance
and stable replay. Nothing is merged; human approval is mandatory.
"""
from __future__ import annotations

from .classification import (
    CLASS_UNSAFE, CLASS_VALIDATED, GATE_FAIL_STATEMENT,
    GATE_PASS_STATEMENT, RESULT_CLASSES, GateCondition,
    classify_result, gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .comparison import (
    artifact_identity, governance_identity,
    measured_runtime_improvement, recompute_counts,
    regression_survival, replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_REAL, VERDICT_UNSAFE,
    V292Report, build_report, build_verdict_artifact,
)


__all__ = [
    "CLASS_UNSAFE",
    "CLASS_VALIDATED",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "RESULT_CLASSES",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "VERDICT_UNSAFE",
    "GateCondition",
    "V292Report",
    "artifact_identity",
    "build_report",
    "build_verdict_artifact",
    "classify_result",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "measured_runtime_improvement",
    "recompute_counts",
    "regression_survival",
    "replay_stability",
]
