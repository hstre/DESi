"""Aufgabe 4 — frozen-stack replay with content-inspection
fields."""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import ExternalChain
from ..external_probe.enums import Domain, GroundTruth
from ..frame_inference import InferenceStrategy
from ..frame_inference.strategies import (
    f4_context_window, is_context_strategy, stateless_strategy,
)
from ..frame_tension import FrameTensionLayer
from ..frame_tension_integration import FrameTensionRouter
from ..frames import FrameDetector, FrameKind
from ..logic.audit import LogicalAuditor
from ..logic.premises import PremiseExtractor
from .cases import ResidueCase


_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were",
    "of", "to", "in", "on", "at", "and", "or", "for",
    "with", "by", "from", "as", "be", "been",
    "this", "that", "these", "those", "it",
    "therefore", "thus", "so", "hence", "than",
})


def _content_tokens(text: str) -> tuple[str, ...]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        s = s.replace(ch, " ")
    return tuple(sorted({
        t for t in s.split()
        if t not in _STOPWORDS and len(t) >= 3
    }))


def _extracted_links(
    premises: tuple, conclusion_text: str,
) -> tuple[str, ...]:
    concl = set(_content_tokens(conclusion_text))
    out: list[str] = []
    for i, p in enumerate(premises):
        shared = sorted(concl & set(_content_tokens(p.text)))
        out.append(
            f"p{i}:" + (",".join(shared) if shared else "-"),
        )
    return tuple(out)


def _support_path(consistency: str, routing_event: str,
                  support_state: str) -> str:
    return f"{consistency}->{routing_event}->{support_state}"


def _originating_strategy(text: str) -> tuple[str, ...]:
    chain = ExternalChain(
        chain_id="probe", domain=Domain.D1_SCIENTIFIC_ABSTRACTS,
        text=text, ground_truth=GroundTruth.INVALID,
        rationale="probe",
    )
    out: list[str] = []
    history: list[tuple[str, FrameKind | None]] = [
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL)
        for _ in range(4)
    ]
    for s in InferenceStrategy:
        if is_context_strategy(s):
            inferred = f4_context_window(
                chain, prior_history=tuple(history),
            )
        else:
            inferred = stateless_strategy(s)(chain)
        if (
            inferred is not None
            and inferred is not FrameKind.FRAME_UNDECLARED
        ):
            out.append(s.value)
    return tuple(out)


@dataclass(frozen=True)
class ReplayRecord:
    chain_id: str
    domain: str
    frame_kind: str
    routing_decision: str
    support_state: str
    premise_tokens: tuple[tuple[str, ...], ...]
    conclusion_tokens: tuple[str, ...]
    overlap_tokens: tuple[str, ...]
    extracted_links: tuple[str, ...]
    support_path: str
    originating_strategy: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "frame_kind": self.frame_kind,
            "routing_decision": self.routing_decision,
            "support_state": self.support_state,
            "premise_tokens": [
                list(t) for t in self.premise_tokens
            ],
            "conclusion_tokens": list(self.conclusion_tokens),
            "overlap_tokens": list(self.overlap_tokens),
            "extracted_links": list(self.extracted_links),
            "support_path": self.support_path,
            "originating_strategy":
                list(self.originating_strategy),
        }


def replay_case(case: ResidueCase) -> ReplayRecord:
    auditor = LogicalAuditor()
    extractor = PremiseExtractor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    extracted = extractor.extract(case.text)
    audit = auditor.audit(case.text)
    decl = detector.detect(
        claim_id=case.chain_id, source_text=case.text,
    )
    gate = layer.gate(
        claim_id=case.chain_id, claim_text=case.text,
        inherited_context_text="",
    )
    route = router.route(
        claim_id=case.chain_id, claim_text=case.text,
        inherited_context_text="",
    )
    conclusion_text = (
        extracted.conclusion.text if extracted.conclusion else ""
    )
    concl_set = set(_content_tokens(conclusion_text))
    premise_token_lists = tuple(
        _content_tokens(p.text) for p in extracted.premises
    )
    overlap = sorted(
        concl_set.intersection(*[
            set(p) for p in premise_token_lists
        ]) if premise_token_lists else set()
    )
    return ReplayRecord(
        chain_id=case.chain_id, domain=case.domain,
        frame_kind=decl.frame_kind.value,
        routing_decision=route.event.value,
        support_state=audit.state.value,
        premise_tokens=premise_token_lists,
        conclusion_tokens=tuple(sorted(concl_set)),
        overlap_tokens=tuple(overlap),
        extracted_links=_extracted_links(
            extracted.premises, conclusion_text,
        ),
        support_path=_support_path(
            gate.consistency.value, route.event.value,
            audit.state.value,
        ),
        originating_strategy=_originating_strategy(case.text),
    )


def replay_all(
    cases: tuple[ResidueCase, ...],
) -> tuple[ReplayRecord, ...]:
    return tuple(replay_case(c) for c in cases)


__all__ = ["ReplayRecord", "replay_all", "replay_case"]
