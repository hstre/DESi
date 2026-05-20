"""DESi v2.0 / v2.2 evolution sandboxes — read-only over stable-v1.9.0."""
from __future__ import annotations

from .depth_events import (
    DepthLedgerEntry,
    DepthLedgerEventType,
    DepthShadowLedger,
)
from .depth_evolution import DepthEvolutionSandbox
from .depth_metrics import (
    KILL_PENALTY,
    DepthImpactMetrics,
    FitnessBreakdown,
    OverreasoningVerdict,
    compute_fitness,
    compute_impact_metrics,
    detect_plateau,
    overreasoning_check,
)
from .depth_mutation import (
    DEFAULT_START_DEPTH,
    DEPTH_MAX,
    DEPTH_MIN,
    DepthMutationProposal,
)
from .depth_report import (
    DepthEvolutionReport,
    DepthStepOutcome,
    DepthStepRecord,
    compute_depth_replay_hash,
)
from .depth_stress import (
    ALL_DEPTH_STRESS_CASES,
    DepthStressCase,
    DepthStressResult,
    DepthStressRun,
    DepthStressSuite,
)
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
    # v2.0
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
    # v2.2 — depth sandbox
    "ALL_DEPTH_STRESS_CASES",
    "DEFAULT_START_DEPTH",
    "DEPTH_MAX",
    "DEPTH_MIN",
    "DepthEvolutionReport",
    "DepthEvolutionSandbox",
    "DepthImpactMetrics",
    "DepthLedgerEntry",
    "DepthLedgerEventType",
    "DepthMutationProposal",
    "DepthShadowLedger",
    "DepthStepOutcome",
    "DepthStepRecord",
    "DepthStressCase",
    "DepthStressResult",
    "DepthStressRun",
    "DepthStressSuite",
    "FitnessBreakdown",
    "KILL_PENALTY",
    "OverreasoningVerdict",
    "compute_depth_replay_hash",
    "compute_fitness",
    "compute_impact_metrics",
    "detect_plateau",
    "overreasoning_check",
]
