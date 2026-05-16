"""Aufgaben 4–7 — simulate the four insertion points.

Each simulator models what the v3.11 FrameTensionLayer would see
if it were invoked at that point in the DESi pipeline. The
**runtime layer is not modified**; we only call it with
different ``(claim_text, inherited_context_text)`` inputs that
reflect what information is available at each insertion point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..frame_tension import (
    FrameConsistency,
    FrameTensionLayer,
    FrameTensionLedgerEvent,
    evaluate_consistency,
)
from ..frames import FrameDetector, FrameKind
from .corpus import CorpusCase
from .enums import InsertionPoint


_FIXED_TIME = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class SimulationOutcome:
    case_id: str
    insertion_point: InsertionPoint
    is_adversarial: bool
    expected_consistency: str | None
    observed_consistency: str
    inherited_allowed: bool
    event: str

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "insertion_point": self.insertion_point.value,
            "is_adversarial": self.is_adversarial,
            "expected_consistency": self.expected_consistency,
            "observed_consistency": self.observed_consistency,
            "inherited_allowed": self.inherited_allowed,
            "event": self.event,
        }


def _gate(layer: FrameTensionLayer, case_id: str, claim_text: str,
          context_text: str) -> tuple[FrameConsistency, bool, str]:
    d = layer.gate(
        claim_id=case_id,
        claim_text=claim_text,
        inherited_context_text=context_text,
        recorded_at=_FIXED_TIME,
    )
    return d.consistency, d.inherited_allowed, d.event.value


def _simulate_pre_spl(case: CorpusCase) -> SimulationOutcome:
    """PRE_SPL: layer sees the raw blob — claim and context glued
    together — because SPL has not yet separated claim sentences
    from surrounding context. The inner and outer textual
    arguments are the *same* combined string."""
    layer = FrameTensionLayer()
    combined = f"{case.inherited_context_text}\n{case.claim_text}".strip()
    cons, allowed, event = _gate(
        layer, case.case_id, combined, combined,
    )
    return SimulationOutcome(
        case_id=case.case_id,
        insertion_point=InsertionPoint.PRE_SPL,
        is_adversarial=case.is_adversarial,
        expected_consistency=(
            case.expected_consistency.value
            if case.expected_consistency else None
        ),
        observed_consistency=cons.value,
        inherited_allowed=allowed,
        event=event,
    )


def _simulate_post_spl_pre_frame(case: CorpusCase) -> SimulationOutcome:
    """POST_SPL_PRE_FRAME: SPL has separated claim from context;
    the layer now runs on (claim_text, inherited_context_text)
    exactly as v3.11 prescribes — but no FrameDeclaration is
    available yet."""
    layer = FrameTensionLayer()
    cons, allowed, event = _gate(
        layer, case.case_id, case.claim_text,
        case.inherited_context_text,
    )
    return SimulationOutcome(
        case_id=case.case_id,
        insertion_point=InsertionPoint.POST_SPL_PRE_FRAME,
        is_adversarial=case.is_adversarial,
        expected_consistency=(
            case.expected_consistency.value
            if case.expected_consistency else None
        ),
        observed_consistency=cons.value,
        inherited_allowed=allowed,
        event=event,
    )


def _simulate_post_frame_pre_routing(case: CorpusCase) -> SimulationOutcome:
    """POST_FRAME_PRE_ROUTING: the v3.4 FrameDetector has already
    produced a declaration. We let the layer evaluate the verdict
    as in POST_SPL — the detector is deterministic so the inner
    side is identical — but we promote the case status when the
    declaration is explicit (non-UNDECLARED). The behaviour
    mirrors what production code would do: trust an explicit
    inner frame declaration, fall back to layer evaluation
    otherwise."""
    detector = FrameDetector()
    inner_decl = detector.detect(
        claim_id=case.case_id, source_text=case.claim_text,
    )

    layer = FrameTensionLayer()
    cons, allowed, event = _gate(
        layer, case.case_id, case.claim_text,
        case.inherited_context_text,
    )

    # If the declaration produced an explicit inner frame and the
    # layer says UNDECIDABLE only because the inner extractor
    # internally fired multiple buckets, the explicit declaration
    # would resolve the ambiguity in production. Surface that as
    # CONFLICT or TENSION based on the verdict's outer side.
    if (
        cons is FrameConsistency.UNDECIDABLE
        and inner_decl.frame_kind is not FrameKind.FRAME_UNDECLARED
    ):
        verdict = evaluate_consistency(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
        )
        if verdict.outer.declared is not None:
            if verdict.outer.declared is inner_decl.frame_kind:
                cons = FrameConsistency.CONFIRMED
                allowed = True
                event = (
                    FrameTensionLedgerEvent.FRAME_INHERITANCE_ALLOWED
                ).value
            else:
                pair = frozenset(
                    {verdict.outer.declared, inner_decl.frame_kind}
                )
                from ..frame_tension.consistency import (
                    _CONFLICT_CAPABLE_PAIRS,
                )
                if pair in _CONFLICT_CAPABLE_PAIRS:
                    cons = FrameConsistency.TENSION
                    event = (
                        FrameTensionLedgerEvent
                        .FRAME_INHERITANCE_BLOCKED
                    ).value
                else:
                    cons = FrameConsistency.CONFLICT
                    event = (
                        FrameTensionLedgerEvent
                        .FRAME_CONFLICT_BLOCKED
                    ).value
                allowed = False

    return SimulationOutcome(
        case_id=case.case_id,
        insertion_point=InsertionPoint.POST_FRAME_PRE_ROUTING,
        is_adversarial=case.is_adversarial,
        expected_consistency=(
            case.expected_consistency.value
            if case.expected_consistency else None
        ),
        observed_consistency=cons.value,
        inherited_allowed=allowed,
        event=event,
    )


def _simulate_post_routing(case: CorpusCase) -> SimulationOutcome:
    """POST_ROUTING: same gate decision as POST_FRAME but invoked
    *after* the claim has already been routed to a downstream
    pipeline. Any block here is a **late block** — the wrong
    pipeline has already seen the claim, so the block has the
    operational shape of an audit, not a gate."""
    upstream = _simulate_post_frame_pre_routing(case)
    return SimulationOutcome(
        case_id=case.case_id,
        insertion_point=InsertionPoint.POST_ROUTING,
        is_adversarial=case.is_adversarial,
        expected_consistency=upstream.expected_consistency,
        observed_consistency=upstream.observed_consistency,
        inherited_allowed=upstream.inherited_allowed,
        event=upstream.event,
    )


_SIMULATORS = {
    InsertionPoint.PRE_SPL: _simulate_pre_spl,
    InsertionPoint.POST_SPL_PRE_FRAME: _simulate_post_spl_pre_frame,
    InsertionPoint.POST_FRAME_PRE_ROUTING: _simulate_post_frame_pre_routing,
    InsertionPoint.POST_ROUTING: _simulate_post_routing,
}


def simulate_all_points(
    corpus: tuple[CorpusCase, ...],
) -> dict[InsertionPoint, tuple[SimulationOutcome, ...]]:
    out: dict[InsertionPoint, tuple[SimulationOutcome, ...]] = {}
    for point, fn in _SIMULATORS.items():
        out[point] = tuple(fn(c) for c in corpus)
    return out


__all__ = [
    "SimulationOutcome",
    "simulate_all_points",
]
