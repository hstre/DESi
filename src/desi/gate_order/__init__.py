"""DESi v3.22 — Gate Order Causality Probe (read-only)."""
from __future__ import annotations

from .corpus import (
    ChainEntry, all_chains, transitions_per_chain,
)
from .enums import Gate, OrderingName, all_orderings, gate_sequence
from .report import (
    GateOrderReport,
    MAX_VALID_BLOCK_RATE,
    MIN_ATTACK_COUNT,
    MIN_CHAIN_COUNT,
    MIN_HELDOUT_RECALL,
    MIN_TRANSITION_COUNT,
    OrderingReport,
    build_gate_order_report,
)
from .simulator import (
    ChainTrace, GateState, OrderMetrics,
    compute_states, run_ordering,
)

__all__ = [
    "ChainEntry",
    "ChainTrace",
    "Gate",
    "GateOrderReport",
    "GateState",
    "MAX_VALID_BLOCK_RATE",
    "MIN_ATTACK_COUNT",
    "MIN_CHAIN_COUNT",
    "MIN_HELDOUT_RECALL",
    "MIN_TRANSITION_COUNT",
    "OrderMetrics",
    "OrderingName",
    "OrderingReport",
    "all_chains",
    "all_orderings",
    "build_gate_order_report",
    "compute_states",
    "gate_sequence",
    "run_ordering",
    "transitions_per_chain",
]
