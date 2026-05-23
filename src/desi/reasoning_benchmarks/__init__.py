"""DESi v36.0 - IFEval Instruction-Following Run (read-only).

Runs a locally-vendored IFEval-format reference dataset through DESi's
deterministic constraint engine: compliant constraints are satisfied
and fabrication requests are refused. Tests constraint enforcement and
refusal governance, not LLM task accuracy.
"""
from __future__ import annotations

from .governance import (
    core_identity, core_replay_stable, governance_identity,
)
from .ifeval_loader import (
    IFEvalTask, dataset_hash, dataset_version, ifeval_tasks,
    provenance,
)
from .ifeval_runner import IFEvalResult, run_all, run_one
from .instruction_constraints import (
    CONSTRAINT_TYPES, generate, must_refuse, satisfies,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V360Report, build_ifeval_artifact, build_report,
    constraint_preservation, format_compliance, ifeval_metrics,
    instruction_following_score, refusal_integrity, replay_stability,
)
from .scorecard import IFEvalScorecard, ifeval_scorecards


__all__ = [
    "CONSTRAINT_TYPES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "IFEvalResult",
    "IFEvalScorecard",
    "IFEvalTask",
    "V360Report",
    "build_ifeval_artifact",
    "build_report",
    "constraint_preservation",
    "core_identity",
    "core_replay_stable",
    "dataset_hash",
    "dataset_version",
    "format_compliance",
    "generate",
    "governance_identity",
    "ifeval_metrics",
    "ifeval_scorecards",
    "ifeval_tasks",
    "instruction_following_score",
    "must_refuse",
    "provenance",
    "refusal_integrity",
    "replay_stability",
    "run_all",
    "run_one",
    "satisfies",
]
