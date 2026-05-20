"""Aufgabe 5 + 6 + 7 — frozen-stack runner + per-chain outcomes."""
from __future__ import annotations

from dataclasses import dataclass

from ..frame_tension import FrameConsistency, FrameTensionLayer
from ..frame_tension_integration import (
    FrameRoutingLedgerEvent, FrameTensionRouter,
)
from ..frames import FrameDetector
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .corpus import ExternalChain
from .enums import FailureClass, GroundTruth


@dataclass(frozen=True)
class ChainOutcome:
    chain_id: str
    domain: str
    ground_truth: str
    audit_state: str
    audit_rule: str | None
    consistency: str
    routing_event: str
    is_supported: bool
    inheritance_allowed: bool
    pipeline_verdict: str
    correct: bool
    failure_class: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "ground_truth": self.ground_truth,
            "audit_state": self.audit_state,
            "audit_rule": self.audit_rule,
            "consistency": self.consistency,
            "routing_event": self.routing_event,
            "is_supported": self.is_supported,
            "inheritance_allowed": self.inheritance_allowed,
            "pipeline_verdict": self.pipeline_verdict,
            "correct": self.correct,
            "failure_class": self.failure_class,
        }


def _pipeline_verdict(
    audit_state: LogicalState, audit_rule: InferenceRule | None,
    consistency: FrameConsistency,
    routing_event: FrameRoutingLedgerEvent,
) -> str:
    """Reduce the four-layer outcome into a single
    VALID / INVALID / UNDECIDABLE verdict."""
    if (
        audit_state is LogicalState.LOGICALLY_SUPPORTED
        and audit_rule is InferenceRule.CAUSAL_CHAIN
        and routing_event is (
            FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED
        )
    ):
        return "VALID"
    if audit_state is LogicalState.LOGICALLY_REJECTED:
        return "INVALID"
    if routing_event is (
        FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
    ):
        return "INVALID"
    return "UNDECIDABLE"


def _classify_failure(
    chain: ExternalChain, verdict: str,
    consistency: FrameConsistency,
    audit_state: LogicalState,
    routing_event: FrameRoutingLedgerEvent,
) -> str | None:
    """Map mispredictions to the directive's closed FailureClass."""
    gt = chain.ground_truth.value
    if verdict == gt:
        return None
    # Pipeline said INVALID but ground truth says VALID
    if gt == "VALID" and verdict == "INVALID":
        if audit_state is LogicalState.LOGICALLY_REJECTED:
            return FailureClass.CHAIN_FAILURE.value
        if routing_event is (
            FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
        ):
            return FailureClass.ROUTING_FAILURE.value
        return FailureClass.SUSPENSION_FAILURE.value
    # Pipeline said VALID but ground truth says INVALID
    if gt == "INVALID" and verdict == "VALID":
        if consistency is FrameConsistency.CONFIRMED:
            return FailureClass.FRAME_FAILURE.value
        return FailureClass.SUSPENSION_FAILURE.value
    # Pipeline said UNDECIDABLE for either polarity
    if verdict == "UNDECIDABLE":
        if consistency is FrameConsistency.UNDECIDABLE:
            return FailureClass.FRAME_FAILURE.value
        return FailureClass.GROUND_TRUTH_MISMATCH.value
    # Pipeline said VALID/INVALID, ground truth says UNDECIDABLE
    if gt == "UNDECIDABLE":
        return FailureClass.GROUND_TRUTH_MISMATCH.value
    return FailureClass.UNKNOWN.value


def run_chain(
    chain: ExternalChain, *,
    auditor: LogicalAuditor,
    detector: FrameDetector,
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
    verdict = _pipeline_verdict(
        audit.state, audit.rule, gate.consistency, route.event,
    )
    correct = verdict == chain.ground_truth.value
    failure_class = None if correct else _classify_failure(
        chain, verdict, gate.consistency,
        audit.state, route.event,
    )
    return ChainOutcome(
        chain_id=chain.chain_id,
        domain=chain.domain.value,
        ground_truth=chain.ground_truth.value,
        audit_state=audit.state.value,
        audit_rule=audit.rule.value if audit.rule else None,
        consistency=gate.consistency.value,
        routing_event=route.event.value,
        is_supported=audit.state is (
            LogicalState.LOGICALLY_SUPPORTED
        ),
        inheritance_allowed=route.inheritance_allowed,
        pipeline_verdict=verdict,
        correct=correct,
        failure_class=failure_class,
    )


def run_all(
    chains: tuple[ExternalChain, ...],
) -> tuple[ChainOutcome, ...]:
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    return tuple(
        run_chain(c, auditor=auditor, detector=detector,
                  layer=layer, router=router)
        for c in chains
    )


__all__ = ["ChainOutcome", "run_all", "run_chain"]
