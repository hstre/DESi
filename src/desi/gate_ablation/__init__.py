"""DESi v3.21 — Gate Ablation Study (read-only)."""
from __future__ import annotations

from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import Gate, GateClassification, ablated_gates
from .negative_control import ALL_NCS, NCCase, NCShape
from .report import (
    DEAD_KNOB_DELTA,
    GateAblation,
    GateAblationReport,
    MIN_ATTACK_COUNT,
    MIN_CHAIN_COUNT,
    MIN_NC_ACCURACY,
    MIN_TRANSITION_COUNT,
    PRIMARY_CLIFF_DELTA,
    build_gate_ablation_report,
)
from .simulator import (
    AblationMetrics, ChainOutcome,
    run_ablation, run_baseline,
)

__all__ = [
    "ALL_NCS",
    "AblationMetrics",
    "ChainEntry",
    "ChainOutcome",
    "DEAD_KNOB_DELTA",
    "Gate",
    "GateAblation",
    "GateAblationReport",
    "GateClassification",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_NC_ACCURACY",
    "MIN_TRANSITION_COUNT",
    "NCCase",
    "NCShape",
    "PRIMARY_CLIFF_DELTA",
    "ablated_gates",
    "all_chains",
    "build_gate_ablation_report",
    "run_ablation",
    "run_baseline",
    "transitions_per_chain",
]
