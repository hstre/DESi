"""DESi v3.23 — Gate Stack Latency Probe (read-only)."""
from __future__ import annotations

from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import (
    EfficiencyClass, StackName, all_stacks, stack_sequence,
)
from .negative_control import (
    ALL_NCS, NCCase, NCShape,
    classify_delta, run_negative_controls,
)
from .report import (
    GateLatencyReport,
    MIN_ATTACK_COUNT,
    MIN_CHAIN_COUNT,
    MIN_NC_ACCURACY,
    MIN_TRANSITION_COUNT,
    StackEvaluation,
    build_gate_latency_report,
)
from .simulator import ChainTrace, StackMetrics, run_stack

__all__ = [
    "ALL_NCS",
    "ChainEntry",
    "ChainTrace",
    "EfficiencyClass",
    "GateLatencyReport",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "NCCase",
    "NCShape",
    "StackEvaluation",
    "StackMetrics",
    "StackName",
    "all_chains",
    "all_stacks",
    "build_gate_latency_report",
    "classify_delta",
    "run_negative_controls",
    "run_stack",
    "stack_sequence",
    "transitions_per_chain",
]
