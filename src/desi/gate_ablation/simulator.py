"""Aufgaben 4 + 5 — gate ablation simulator + per-metric measurement.

Each gate is ablated by *predicting* the pipeline outcome if
the gate were a pass-through. No runtime modification — the
real pipeline stays untouched. Predictions are deterministic
and grounded in the existing module behaviour:

* G1 / G2 (PremiseExtractor / SPL) — without sentence splitting
  no rule can match, audit defaults to GAP_DETECTED.
* G3 (FrameDeclaration) — frame stays UNDECLARED everywhere, so
  the FrameTension verdict collapses to UNDECIDABLE.
* G4 (FrameTension) — always emits CONFIRMED.
* G5 (Router) — always emits FRAME_ROUTING_ALLOWED.
* G6 (CAUSAL_CHAIN) — the rule cannot match; chains end at
  GAP_DETECTED / BRIDGE_REQUIRED.
* G7 (SuspensionGate) — the v3.16 marker extensions are
  removed; the v2.7 baseline rule matches every adversarial
  that bypassed v2.7's marker tuples (v3.15 corpus by
  construction).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frame_tension import FrameConsistency, FrameTensionLayer
from ..frame_tension_integration import (
    FrameRoutingLedgerEvent, FrameTensionRouter,
)
from ..frames import FrameDetector
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .corpus import ChainEntry
from .enums import Gate


@dataclass(frozen=True)
class ChainOutcome:
    chain_id: str
    is_attack: bool
    support_state: str    # LogicalState value
    is_supported: bool
    consistency: str      # FrameConsistency value
    routing_event: str    # FrameRoutingLedgerEvent value
    inheritance_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "is_attack": self.is_attack,
            "support_state": self.support_state,
            "is_supported": self.is_supported,
            "consistency": self.consistency,
            "routing_event": self.routing_event,
            "inheritance_allowed": self.inheritance_allowed,
        }


def _baseline_for(
    chain: ChainEntry, *,
    auditor: LogicalAuditor,
    layer: FrameTensionLayer,
    router: FrameTensionRouter,
) -> ChainOutcome:
    audit = auditor.audit(chain.text)
    gate = layer.gate(
        claim_id=chain.chain_id, claim_text=chain.text,
        inherited_context_text="",
    )
    route = router.route(
        claim_id=chain.chain_id, claim_text=chain.text,
        inherited_context_text="",
    )
    is_supported = (
        audit.state == LogicalState.LOGICALLY_SUPPORTED
        and audit.rule is InferenceRule.CAUSAL_CHAIN
    )
    return ChainOutcome(
        chain_id=chain.chain_id, is_attack=chain.is_attack,
        support_state=audit.state.value,
        is_supported=is_supported,
        consistency=gate.consistency.value,
        routing_event=route.event.value,
        inheritance_allowed=route.inheritance_allowed,
    )


def _ablated_for(
    chain: ChainEntry, baseline: ChainOutcome, gate: Gate,
) -> ChainOutcome:
    """Predict the pipeline outcome under ablation of ``gate``.

    The prediction is a closed mapping over the baseline plus
    chain-level evidence; no runtime call is made under masking.
    """
    if gate is Gate.G1_PREMISE_EXTRACTOR:
        # No premises -> no rule match -> GAP_DETECTED. Tension
        # layer can still see context (none here) so it would
        # return UNDECIDABLE. Router would refuse.
        return ChainOutcome(
            chain_id=chain.chain_id, is_attack=chain.is_attack,
            support_state="gap_detected", is_supported=False,
            consistency="undecidable",
            routing_event="frame_routing_marker_required",
            inheritance_allowed=False,
        )
    if gate is Gate.G2_SPL:
        # SPL == sentence splitting; without it the text is one
        # premise and audit fails the same way as G1.
        return ChainOutcome(
            chain_id=chain.chain_id, is_attack=chain.is_attack,
            support_state="gap_detected", is_supported=False,
            consistency="undecidable",
            routing_event="frame_routing_marker_required",
            inheritance_allowed=False,
        )
    if gate is Gate.G3_FRAME_DECLARATION:
        # Frame stays UNDECLARED -> FrameTension collapses to
        # UNDECIDABLE -> router refuses. Audit itself is
        # unchanged because LogicalAuditor does not consult
        # FrameDetector.
        return ChainOutcome(
            chain_id=chain.chain_id, is_attack=chain.is_attack,
            support_state=baseline.support_state,
            is_supported=baseline.is_supported,
            consistency="undecidable",
            routing_event="frame_routing_marker_required",
            inheritance_allowed=False,
        )
    if gate is Gate.G4_FRAME_TENSION:
        # Tension layer always returns CONFIRMED -> router
        # ALLOWED -> inheritance allowed.
        return ChainOutcome(
            chain_id=chain.chain_id, is_attack=chain.is_attack,
            support_state=baseline.support_state,
            is_supported=baseline.is_supported,
            consistency="confirmed",
            routing_event="frame_routing_allowed",
            inheritance_allowed=True,
        )
    if gate is Gate.G5_ROUTER:
        # Router always allowed; tension verdict preserved.
        return ChainOutcome(
            chain_id=chain.chain_id, is_attack=chain.is_attack,
            support_state=baseline.support_state,
            is_supported=baseline.is_supported,
            consistency=baseline.consistency,
            routing_event="frame_routing_allowed",
            inheritance_allowed=True,
        )
    if gate is Gate.G6_CAUSAL_CHAIN:
        # CAUSAL_CHAIN cannot fire; audit ends at GAP_DETECTED
        # or one of the other rules (SYLLOGISM / CONTRADICTION
        # etc.). Conservatively: any case that *was* supported
        # via CAUSAL_CHAIN at baseline now is GAP_DETECTED.
        if baseline.is_supported:
            return ChainOutcome(
                chain_id=chain.chain_id, is_attack=chain.is_attack,
                support_state="gap_detected", is_supported=False,
                consistency=baseline.consistency,
                routing_event=baseline.routing_event,
                inheritance_allowed=baseline.inheritance_allowed,
            )
        # Otherwise no change: the rule was not matching anyway.
        return baseline
    if gate is Gate.G7_SUSPENSION_GATE:
        # v3.16 marker extensions removed: every attack that the
        # *v2.7 baseline* rule would have supported becomes
        # supported again. The v3.15 adversarial corpus was
        # constructed precisely so v2.7's tuples missed it, so
        # every v3.15 chain — whether currently surviving or
        # currently suspended — would be supported under G7
        # ablation.
        if chain.is_attack and chain.source in (
            "v315_adversarial", "v316_surviving",
            "v316_suspended", "v321_adversarial_view",
        ):
            return ChainOutcome(
                chain_id=chain.chain_id, is_attack=True,
                support_state="logically_supported",
                is_supported=True,
                consistency=baseline.consistency,
                routing_event=baseline.routing_event,
                inheritance_allowed=baseline.inheritance_allowed,
            )
        return baseline
    return baseline


@dataclass(frozen=True)
class AblationMetrics:
    gate: str
    attack_success_rate: float
    heldout_recall: float
    false_positive_count: int
    contamination_count: int
    trajectory_separability: float
    routing_integrity: float
    manipulation_absorption: float

    def feature_tuple(self) -> tuple[float, ...]:
        return (
            self.attack_success_rate,
            self.heldout_recall,
            float(self.false_positive_count),
            float(self.contamination_count),
            self.trajectory_separability,
            self.routing_integrity,
            self.manipulation_absorption,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate,
            "attack_success_rate": self.attack_success_rate,
            "heldout_recall": self.heldout_recall,
            "false_positive_count": self.false_positive_count,
            "contamination_count": self.contamination_count,
            "trajectory_separability": self.trajectory_separability,
            "routing_integrity": self.routing_integrity,
            "manipulation_absorption": self.manipulation_absorption,
        }


def _compute_metrics(
    gate: Gate, outcomes: tuple[ChainOutcome, ...],
) -> AblationMetrics:
    attacks = [o for o in outcomes if o.is_attack]
    valid = [o for o in outcomes if not o.is_attack]
    n_attacks = max(1, len(attacks))
    n_valid = max(1, len(valid))

    attack_success_rate = round(
        sum(1 for o in attacks if o.is_supported) / n_attacks, 6,
    )
    heldout_recall = round(
        sum(1 for o in valid if o.is_supported) / n_valid, 6,
    )
    false_positives = sum(
        1 for o in valid
        if o.support_state == "logically_rejected"
    )
    contamination = sum(
        1 for o in attacks
        if o.routing_event == "frame_routing_allowed"
    )
    # Trajectory separability proxy: difference between attack
    # support rate and valid support rate (saturated to [0,1]).
    raw = abs(heldout_recall - attack_success_rate)
    trajectory_separability = round(min(1.0, raw), 6)
    # Routing integrity: fraction of routing decisions that
    # were not silently allowed for attacks.
    blocked_attacks = sum(
        1 for o in attacks
        if o.routing_event != "frame_routing_allowed"
    )
    routing_integrity = round(blocked_attacks / n_attacks, 6)
    # Manipulation absorption: fraction of attacks that
    # inherited the outer frame (= silently routed).
    manipulation_absorption = round(
        sum(1 for o in attacks if o.inheritance_allowed)
        / n_attacks, 6,
    )

    return AblationMetrics(
        gate=gate.value,
        attack_success_rate=attack_success_rate,
        heldout_recall=heldout_recall,
        false_positive_count=false_positives,
        contamination_count=contamination,
        trajectory_separability=trajectory_separability,
        routing_integrity=routing_integrity,
        manipulation_absorption=manipulation_absorption,
    )


def run_baseline(chains: tuple[ChainEntry, ...]) -> tuple[
    AblationMetrics, tuple[ChainOutcome, ...],
]:
    auditor = LogicalAuditor()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    outs = tuple(
        _baseline_for(c, auditor=auditor, layer=layer, router=router)
        for c in chains
    )
    return _compute_metrics(Gate.BASELINE, outs), outs


def run_ablation(
    gate: Gate,
    chains: tuple[ChainEntry, ...],
    baselines: tuple[ChainOutcome, ...],
) -> AblationMetrics:
    assert len(chains) == len(baselines)
    outs = tuple(
        _ablated_for(c, b, gate)
        for c, b in zip(chains, baselines)
    )
    return _compute_metrics(gate, outs)


__all__ = [
    "AblationMetrics",
    "ChainOutcome",
    "run_ablation",
    "run_baseline",
]
