"""Aufgaben 4 + 5 — per-stack simulator with latency metrics.

Re-uses the v3.22 ``GateState`` + ``_gate_blocks`` predicates
and adds per-gate cost weights so latency_cost reflects real
runtime cost differences (LogicalAuditor and Consilium are
expensive; FrameDetector / extractor are cheap).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..gate_order import Gate, compute_states, run_ordering
from ..gate_order.enums import OrderingName, gate_sequence
from ..gate_order.simulator import GateState, _gate_blocks
from .corpus import ChainEntry
from .enums import StackName, stack_sequence


# Approximate compute cost per gate (in "unit ops"). The
# numbers are deliberate ranks, not micro-benchmarks: they
# reflect the relative depth of each gate's downstream
# pipeline.
_GATE_COST: dict[Gate, float] = {
    Gate.G1_PREMISE_EXTRACTOR: 1.0,
    Gate.G2_SPL:               0.5,
    Gate.G3_FRAME_DECLARATION: 1.0,
    Gate.G4_FRAME_TENSION:     2.0,
    Gate.G5_ROUTER:            2.5,
    Gate.G6_CAUSAL_CHAIN:      4.0,   # LogicalAuditor + ProofChain
    Gate.G7_SUSPENSION_GATE:   1.5,
}


# Downstream-pipeline tags for the saved-calls metrics.
_GATE_PIPELINE: dict[Gate, str] = {
    Gate.G1_PREMISE_EXTRACTOR: "extractor",
    Gate.G2_SPL:               "extractor",
    Gate.G3_FRAME_DECLARATION: "framing",
    Gate.G4_FRAME_TENSION:     "routing",
    Gate.G5_ROUTER:            "routing",
    Gate.G6_CAUSAL_CHAIN:      "audit",
    Gate.G7_SUSPENSION_GATE:   "audit",
}


@dataclass(frozen=True)
class ChainTrace:
    chain_id: str
    is_attack: bool
    fired_gate: str | None
    fire_index: int
    gate_calls: int
    cost: float
    pipelines_visited: tuple[str, ...]
    final_supported: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "is_attack": self.is_attack,
            "fired_gate": self.fired_gate,
            "fire_index": self.fire_index,
            "gate_calls": self.gate_calls,
            "cost": self.cost,
            "pipelines_visited": list(self.pipelines_visited),
            "final_supported": self.final_supported,
        }


def _simulate_chain(
    chain: ChainEntry, state: GateState,
    sequence: tuple[Gate, ...],
) -> ChainTrace:
    visited: list[str] = []
    cost = 0.0
    for idx, gate in enumerate(sequence):
        visited.append(_GATE_PIPELINE[gate])
        cost += _GATE_COST[gate]
        if _gate_blocks(gate, state, chain):
            return ChainTrace(
                chain_id=chain.chain_id,
                is_attack=chain.is_attack,
                fired_gate=gate.value,
                fire_index=idx,
                gate_calls=idx + 1,
                cost=round(cost, 6),
                pipelines_visited=tuple(visited),
                final_supported=False,
            )
    return ChainTrace(
        chain_id=chain.chain_id,
        is_attack=chain.is_attack,
        fired_gate=None,
        fire_index=len(sequence),
        gate_calls=len(sequence),
        cost=round(cost, 6),
        pipelines_visited=tuple(visited),
        final_supported=True,
    )


@dataclass(frozen=True)
class StackMetrics:
    stack: str
    attack_success_rate: float
    heldout_recall: float
    false_route_count: int
    contamination_count: int
    average_gate_depth: float
    gate_calls_total: int
    tool_calls_saved: int
    audit_calls_saved: int
    consilium_calls_saved: int
    routing_calls_saved: int
    latency_cost: float

    def to_dict(self) -> dict[str, object]:
        return {
            "stack": self.stack,
            "attack_success_rate": self.attack_success_rate,
            "heldout_recall": self.heldout_recall,
            "false_route_count": self.false_route_count,
            "contamination_count": self.contamination_count,
            "average_gate_depth": self.average_gate_depth,
            "gate_calls_total": self.gate_calls_total,
            "tool_calls_saved": self.tool_calls_saved,
            "audit_calls_saved": self.audit_calls_saved,
            "consilium_calls_saved": self.consilium_calls_saved,
            "routing_calls_saved": self.routing_calls_saved,
            "latency_cost": self.latency_cost,
        }


def _metrics_for(
    name: StackName, traces: tuple[ChainTrace, ...],
    sequence: tuple[Gate, ...],
) -> StackMetrics:
    attacks = [t for t in traces if t.is_attack]
    valid = [t for t in traces if not t.is_attack]
    n_attacks = max(1, len(attacks))
    n_valid = max(1, len(valid))

    attack_success = sum(1 for t in attacks if t.final_supported)
    valid_supported = sum(1 for t in valid if t.final_supported)

    # false_route_count: attacks that survive past FrameTension
    # AND Router stages (in this sequence).
    g4_idx = sequence.index(Gate.G4_FRAME_TENSION) if (
        Gate.G4_FRAME_TENSION in sequence
    ) else -1
    g5_idx = sequence.index(Gate.G5_ROUTER) if (
        Gate.G5_ROUTER in sequence
    ) else -1
    cutoff = max(g4_idx, g5_idx) + 1
    false_routes = sum(1 for t in attacks if t.fire_index >= cutoff)
    contamination = attack_success

    # Pipeline-saved counts: every gate the chain DID NOT call
    # because it terminated early. We attribute the savings to
    # the downstream-pipeline tag of each not-called gate.
    extractor_saved = 0
    framing_saved = 0
    routing_saved = 0
    audit_saved = 0
    for t in traces:
        not_called = sequence[t.gate_calls:]
        for g in not_called:
            pipe = _GATE_PIPELINE[g]
            if pipe == "extractor":
                extractor_saved += 1
            elif pipe == "framing":
                framing_saved += 1
            elif pipe == "routing":
                routing_saved += 1
            elif pipe == "audit":
                audit_saved += 1

    average_gate_depth = (
        round(sum(t.gate_calls for t in traces) / len(traces), 6)
        if traces else 0.0
    )
    gate_calls_total = sum(t.gate_calls for t in traces)
    latency_cost = round(
        sum(t.cost for t in traces) / max(1, len(traces)), 6,
    )

    return StackMetrics(
        stack=name.value,
        attack_success_rate=round(
            attack_success / n_attacks, 6,
        ),
        heldout_recall=round(valid_supported / n_valid, 6),
        false_route_count=false_routes,
        contamination_count=contamination,
        average_gate_depth=average_gate_depth,
        gate_calls_total=gate_calls_total,
        tool_calls_saved=extractor_saved,
        audit_calls_saved=audit_saved,
        consilium_calls_saved=framing_saved,
        routing_calls_saved=routing_saved,
        latency_cost=latency_cost,
    )


def run_stack(
    name: StackName, chains: tuple[ChainEntry, ...],
    states: tuple[GateState, ...],
) -> tuple[StackMetrics, tuple[ChainTrace, ...]]:
    sequence = stack_sequence(name)
    traces = tuple(
        _simulate_chain(c, s, sequence)
        for c, s in zip(chains, states)
    )
    return _metrics_for(name, traces, sequence), traces


__all__ = [
    "ChainTrace",
    "StackMetrics",
    "compute_states",
    "run_stack",
]
