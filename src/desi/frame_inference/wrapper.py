"""Aufgabe 5/6 — external pipeline wrapper.

Given an inferred ``FrameKind`` (or ``None``) for an
``ExternalChain``, run the chain through the *frozen* v3.13
pipeline (``LogicalAuditor`` + ``FrameTensionLayer`` +
``FrameTensionRouter``) by synthesising a ``Frame:`` marker
into the routing layer's input. The audit always sees the
original chain text — frame inference never injects words
into the chain for the auditor's eyes.

This wrapper is read-only: it constructs strings to pass to the
existing runtime, but never patches or imports a private
symbol from ``logic/``, ``frames/``, ``frame_tension/`` or
``frame_tension_integration/``.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import ExternalChain
from ..external_probe.enums import FailureClass
from ..external_probe.runner import (
    ChainOutcome, _classify_failure, _pipeline_verdict,
)
from ..frame_tension import FrameTensionLayer
from ..frame_tension_integration import FrameTensionRouter
from ..frames import FrameDetector, FrameKind
from ..logic.audit import LogicalAuditor


# Canonical lower-case markers for every non-undeclared frame.
# These match the substrings consumed by
# ``FrameDetector._explicit_marker`` so that the synthetic
# ``Frame: X`` string is recognised by the unmodified detector.
_MARKERS: dict[FrameKind, str] = {
    FrameKind.THERMODYNAMIC:                 "thermodynamic",
    FrameKind.INFORMATION_THEORETIC:         "information-theoretic",
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: "ontological "
                                              "distinguishability",
    FrameKind.METAPHORICAL:                  "metaphorical",
    FrameKind.FORMAL_LOGIC:                  "formal logic",
    FrameKind.EMPIRICAL_CAUSAL:              "empirical causal",
    FrameKind.AUTHORITY_SPEECH:              "authority",
    FrameKind.TOOL_COMPUTABLE:               "tool computable",
}


def synthetic_marker(kind: FrameKind) -> str:
    """Return the ``Frame: <name>`` string the v3.4 detector
    will pick up. ``FRAME_UNDECLARED`` has no synthetic form
    and is rejected here so the caller cannot accidentally
    ingest the default sentinel as if it were a real frame.
    """
    if kind is FrameKind.FRAME_UNDECLARED:
        raise ValueError(
            "FRAME_UNDECLARED has no synthetic marker"
        )
    return f"Frame: {_MARKERS[kind]}"


@dataclass(frozen=True)
class WrappedOutcome:
    """Result of running one chain through the frozen pipeline
    with an inferred frame injected at the routing boundary."""

    inferred_frame: str | None
    outcome: ChainOutcome


def evaluate_chain(
    chain: ExternalChain,
    inferred: FrameKind | None,
    *,
    auditor: LogicalAuditor,
    detector: FrameDetector,
    layer: FrameTensionLayer,
    router: FrameTensionRouter,
) -> WrappedOutcome:
    """Run the frozen pipeline. When ``inferred`` is ``None`` or
    ``FRAME_UNDECLARED`` this mirrors the v4.0 runner exactly.

    Otherwise, we synthesise a ``Frame: X`` marker and pass it
    as *both* the inherited outer context and a prefix on the
    claim text fed to the router. The auditor still receives
    the untouched chain text — so the audit verdict (and its
    contribution to the recall figure) is the same call the v4.0
    runner made.
    """
    audit = auditor.audit(chain.text)
    if inferred is None or inferred is FrameKind.FRAME_UNDECLARED:
        decorated_claim = chain.text
        inherited = ""
    else:
        marker = synthetic_marker(inferred)
        decorated_claim = f"{marker}. {chain.text}"
        inherited = marker
    gate = layer.gate(
        claim_id=chain.chain_id,
        claim_text=decorated_claim,
        inherited_context_text=inherited,
    )
    route = router.route(
        claim_id=chain.chain_id,
        claim_text=decorated_claim,
        inherited_context_text=inherited,
    )
    verdict = _pipeline_verdict(
        audit.state, audit.rule, gate.consistency, route.event,
    )
    correct = verdict == chain.ground_truth.value
    failure_class: str | None
    if correct:
        failure_class = None
    else:
        failure_class = _classify_failure(
            chain, verdict, gate.consistency,
            audit.state, route.event,
        )
    outcome = ChainOutcome(
        chain_id=chain.chain_id,
        domain=chain.domain.value,
        ground_truth=chain.ground_truth.value,
        audit_state=audit.state.value,
        audit_rule=audit.rule.value if audit.rule else None,
        consistency=gate.consistency.value,
        routing_event=route.event.value,
        is_supported=audit.state.value == "logically_supported",
        inheritance_allowed=route.inheritance_allowed,
        pipeline_verdict=verdict,
        correct=correct,
        failure_class=failure_class,
    )
    return WrappedOutcome(
        inferred_frame=(
            inferred.value if inferred is not None else None
        ),
        outcome=outcome,
    )


__all__ = [
    "WrappedOutcome",
    "evaluate_chain",
    "synthetic_marker",
]
