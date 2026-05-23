"""Per-order simulator + 8 metrics.

A chain is fed through the ordered gate sequence. Each gate
either passes the chain forward (next gate) or blocks it
(terminal). The metrics measure the final disposition relative
to the chain's ground-truth label (valid vs attack).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..frame_tension import FrameConsistency, FrameTensionLayer
from ..frame_tension_integration import (
    FrameRoutingLedgerEvent, FrameTensionRouter,
)
from ..frames import FrameDetector, FrameKind
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .corpus import ChainEntry
from .enums import Gate, OrderingName, gate_sequence


@dataclass(frozen=True)
class GateState:
    """Cached pipeline outputs reused across orderings."""

    has_premises: bool
    has_explicit_chain: bool
    declared_frame: FrameKind
    consistency: FrameConsistency
    routing_event: FrameRoutingLedgerEvent
    inheritance_allowed: bool
    audit_state: LogicalState
    audit_rule_is_causal: bool
    suspension_would_block: bool


def _compute_state(
    chain: ChainEntry, *,
    auditor: LogicalAuditor, detector: FrameDetector,
    layer: FrameTensionLayer, router: FrameTensionRouter,
) -> GateState:
    audit = auditor.audit(chain.text)
    detect = detector.detect(
        claim_id=chain.chain_id, source_text=chain.text,
    )
    gate = layer.gate(
        claim_id=chain.chain_id, claim_text=chain.text,
        inherited_context_text="",
    )
    route = router.route(
        claim_id=chain.chain_id, claim_text=chain.text,
        inherited_context_text="",
    )
    # SuspensionGate would block iff the current LogicalAuditor
    # would NOT support the chain as CAUSAL_CHAIN (the gate's
    # only effect is to suspend marker-bearing attacks before
    # the rule fires; if the rule does not fire anyway, the
    # gate is a no-op for that chain).
    is_supported = (
        audit.state == LogicalState.LOGICALLY_SUPPORTED
        and audit.rule is InferenceRule.CAUSAL_CHAIN
    )
    return GateState(
        has_premises=len(audit.propositions.premises) > 0,
        has_explicit_chain=audit.propositions.has_explicit_chain,
        declared_frame=detect.frame_kind,
        consistency=gate.consistency,
        routing_event=route.event,
        inheritance_allowed=route.inheritance_allowed,
        audit_state=audit.state,
        audit_rule_is_causal=is_supported,
        # Suspension blocks adversarial-marker chains.
        suspension_would_block=chain.is_attack and not is_supported,
    )


def _gate_blocks(gate: Gate, state: GateState,
                 chain: ChainEntry) -> bool:
    """Per-gate prediction: does this gate stop the chain?"""
    if gate is Gate.G1_PREMISE_EXTRACTOR:
        return not state.has_premises
    if gate is Gate.G2_SPL:
        return not state.has_explicit_chain
    if gate is Gate.G3_FRAME_DECLARATION:
        # Frame declaration never blocks alone; it produces a
        # value that other gates consume.
        return False
    if gate is Gate.G4_FRAME_TENSION:
        # Blocks ONLY when a real inner/outer mismatch is
        # detected: TENSION or CONFLICT. UNDECIDABLE is "no
        # outer to compare against" and falls through to the
        # downstream gates rather than terminating here.
        return state.consistency in (
            FrameConsistency.TENSION,
            FrameConsistency.CONFLICT,
        )
    if gate is Gate.G5_ROUTER:
        # Blocks the strict failure events. MARKER_REQUIRED
        # (UNDECIDABLE upstream) and INNER_ONLY are
        # downstream-routable.
        return state.routing_event is (
            FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
        )
    if gate is Gate.G6_CAUSAL_CHAIN:
        # The chain rule "blocks" non-CAUSAL chains in the
        # sense that it fails to support them; for the ordering
        # simulator we treat "rule does not match" as a block.
        return not state.audit_rule_is_causal
    if gate is Gate.G7_SUSPENSION_GATE:
        return state.suspension_would_block
    return False


@dataclass(frozen=True)
class ChainTrace:
    chain_id: str
    is_attack: bool
    fired_gate: str | None
    fire_index: int
    final_supported: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "is_attack": self.is_attack,
            "fired_gate": self.fired_gate,
            "fire_index": self.fire_index,
            "final_supported": self.final_supported,
        }


def _simulate_chain(
    chain: ChainEntry, state: GateState,
    sequence: tuple[Gate, ...],
) -> ChainTrace:
    for idx, gate in enumerate(sequence):
        if _gate_blocks(gate, state, chain):
            return ChainTrace(
                chain_id=chain.chain_id, is_attack=chain.is_attack,
                fired_gate=gate.value, fire_index=idx,
                final_supported=False,
            )
    return ChainTrace(
        chain_id=chain.chain_id, is_attack=chain.is_attack,
        fired_gate=None, fire_index=len(sequence),
        final_supported=True,
    )


@dataclass(frozen=True)
class OrderMetrics:
    ordering: str
    attack_success_rate: float
    heldout_recall: float
    false_route_count: int
    valid_block_rate: float
    manipulation_absorption_rate: float
    contamination_count: int
    latency_cost: float
    gate_fire_order_entropy: float

    def to_dict(self) -> dict[str, object]:
        return {
            "ordering": self.ordering,
            "attack_success_rate": self.attack_success_rate,
            "heldout_recall": self.heldout_recall,
            "false_route_count": self.false_route_count,
            "valid_block_rate": self.valid_block_rate,
            "manipulation_absorption_rate":
                self.manipulation_absorption_rate,
            "contamination_count": self.contamination_count,
            "latency_cost": self.latency_cost,
            "gate_fire_order_entropy":
                self.gate_fire_order_entropy,
        }


def _entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c == 0:
            continue
        p = c / total
        h -= p * math.log2(p)
    return h


def _metrics_for(
    ordering: OrderingName, traces: tuple[ChainTrace, ...],
    sequence: tuple[Gate, ...],
) -> OrderMetrics:
    attacks = [t for t in traces if t.is_attack]
    valid = [t for t in traces if not t.is_attack]
    n_attacks = max(1, len(attacks))
    n_valid = max(1, len(valid))

    attack_success = sum(1 for t in attacks if t.final_supported)
    valid_supported = sum(1 for t in valid if t.final_supported)
    valid_blocked = len(valid) - valid_supported

    # false_route_count: adversarial chains that pass FrameTension
    # AND Router stages (i.e., still alive after those gates fire)
    # — meaning the misleading outer would have routed.
    false_routes = 0
    g4_index = (
        sequence.index(Gate.G4_FRAME_TENSION)
        if Gate.G4_FRAME_TENSION in sequence else -1
    )
    g5_index = (
        sequence.index(Gate.G5_ROUTER)
        if Gate.G5_ROUTER in sequence else -1
    )
    cutoff = max(g4_index, g5_index) + 1
    for t in attacks:
        if t.fire_index >= cutoff:
            false_routes += 1

    # Manipulation absorption rate: attacks that reach the end
    # of the sequence (fully supported).
    absorption_rate = round(attack_success / n_attacks, 6)

    # Contamination: attacks that are SUPPORTED at the end (a
    # stricter view of false_routes).
    contamination = attack_success

    # Latency cost: average index at which each chain terminates
    # (lower = cheaper; gates that block early reduce cost).
    if traces:
        latency_cost = round(
            sum(t.fire_index for t in traces) / len(traces), 6,
        )
    else:
        latency_cost = 0.0

    # Entropy of which gate is first to fire across the corpus.
    counts: dict[str, int] = {}
    for t in traces:
        key = t.fired_gate or "PASSED"
        counts[key] = counts.get(key, 0) + 1
    entropy_val = round(_entropy(counts), 6)

    return OrderMetrics(
        ordering=ordering.value,
        attack_success_rate=round(
            attack_success / n_attacks, 6,
        ),
        heldout_recall=round(valid_supported / n_valid, 6),
        false_route_count=false_routes,
        valid_block_rate=round(valid_blocked / n_valid, 6),
        manipulation_absorption_rate=absorption_rate,
        contamination_count=contamination,
        latency_cost=latency_cost,
        gate_fire_order_entropy=entropy_val,
    )


def run_ordering(
    ordering: OrderingName, chains: tuple[ChainEntry, ...],
    states: tuple[GateState, ...],
) -> tuple[OrderMetrics, tuple[ChainTrace, ...]]:
    sequence = gate_sequence(ordering)
    traces = tuple(
        _simulate_chain(c, s, sequence)
        for c, s in zip(chains, states)
    )
    return _metrics_for(ordering, traces, sequence), traces


def compute_states(
    chains: tuple[ChainEntry, ...],
) -> tuple[GateState, ...]:
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    return tuple(
        _compute_state(
            c, auditor=auditor, detector=detector,
            layer=layer, router=router,
        )
        for c in chains
    )


__all__ = [
    "ChainTrace",
    "GateState",
    "OrderMetrics",
    "compute_states",
    "run_ordering",
]
