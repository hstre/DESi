"""Tool Evidence Layer (v1.9).

When a claim is deterministically computable or verifiable, DESi
must use a controlled tool — not language. The package ships:

* a closed :class:`ToolKind` allowlist of 6 kinds;
* a pattern-based :class:`ToolDetector` that proposes a
  :class:`ToolUseProposal` only on tightly-shaped inputs;
* a :class:`ToolGate` with six pre-execution safety checks;
* per-execution :class:`ToolProvenance` (mandatory for every
  result before it can attach to a claim);
* :class:`ImpactScan` + :class:`ContaminationPropagation` for
  registry-based "which-claims-depend-on-tool-X" queries;
* a 20-case mini-benchmark across A/B/C/D/E categories.

The directive: tools never short-circuit to LOGICALLY_SUPPORTED.
A tool result is *evidence* — never authority.
"""
from __future__ import annotations

from .benchmark import (
    ALL_TOOL_CASES,
    ToolBenchmarkCase,
    ToolBenchmarkResult,
    ToolBenchmarkRun,
    ToolBenchmarkRunner,
    ToolCategory,
    ToolGroundTruth,
    cases_by_category,
)
from .detector import ToolDetector
from .gate import (
    FailureReason,
    HARD_TIMEOUT_SECONDS,
    MAX_INPUT_BYTES,
    ToolGate,
    ToolResult,
)
from .impact import (
    ContaminationPropagation,
    ImpactScan,
    ToolUsageRecord,
    ToolUsageRegistry,
)
from .kinds import ALLOWED_TOOL_KINDS, ToolKind
from .proposal import ToolUseProposal, make_run_id
from .provenance import (
    ToolProvenance,
    dependency_fingerprint,
    environment_hash,
)
from .runners import RUNNERS

__all__ = [
    "ALLOWED_TOOL_KINDS",
    "ALL_TOOL_CASES",
    "ContaminationPropagation",
    "FailureReason",
    "HARD_TIMEOUT_SECONDS",
    "ImpactScan",
    "MAX_INPUT_BYTES",
    "RUNNERS",
    "ToolBenchmarkCase",
    "ToolBenchmarkResult",
    "ToolBenchmarkRun",
    "ToolBenchmarkRunner",
    "ToolCategory",
    "ToolDetector",
    "ToolGate",
    "ToolGroundTruth",
    "ToolKind",
    "ToolProvenance",
    "ToolResult",
    "ToolUsageRecord",
    "ToolUsageRegistry",
    "ToolUseProposal",
    "cases_by_category",
    "dependency_fingerprint",
    "environment_hash",
    "make_run_id",
]
