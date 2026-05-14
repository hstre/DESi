"""DESi v2.0 evolution sandbox — read-only over stable-v1.9.0."""
from __future__ import annotations

from .evolution import EvolutionSandbox
from .gate import (
    REQUIRED_AUTHORITY_BLOCKS,
    REQUIRED_PRECISION,
    REQUIRED_RECALL,
    REQUIRED_TOOL_PRECISION,
    GateVerdict,
    SandboxBenchmarkGate,
)
from .ledger import ShadowLedger, ShadowLedgerEntry, ShadowLedgerEventType
from .mutation import (
    BASELINE_VALUE,
    DELTA,
    MAX_VALUE,
    MIN_VALUE,
    MUTABLE_PARAMETER,
    MutationProposal,
)
from .report import (
    EvolutionReport,
    StepOutcome,
    StepRecord,
    compute_replay_hash,
    detect_convergence,
    detect_drift,
    detect_local_optimum,
    detect_oscillation,
)

__all__ = [
    "BASELINE_VALUE",
    "DELTA",
    "EvolutionReport",
    "EvolutionSandbox",
    "GateVerdict",
    "MAX_VALUE",
    "MIN_VALUE",
    "MUTABLE_PARAMETER",
    "MutationProposal",
    "REQUIRED_AUTHORITY_BLOCKS",
    "REQUIRED_PRECISION",
    "REQUIRED_RECALL",
    "REQUIRED_TOOL_PRECISION",
    "SandboxBenchmarkGate",
    "ShadowLedger",
    "ShadowLedgerEntry",
    "ShadowLedgerEventType",
    "StepOutcome",
    "StepRecord",
    "compute_replay_hash",
    "detect_convergence",
    "detect_drift",
    "detect_local_optimum",
    "detect_oscillation",
]
