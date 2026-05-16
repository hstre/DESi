"""Aufgabe 4 — frozen-stack replay.

For every false-support case the replay records the full
``SPL → FrameDeclaration → FrameTension → FrameTensionRouter
→ CAUSAL_CHAIN → SuspensionGate`` trace, plus the v4.1
``frame_strategy_origin`` (which strategies unlocked this case).

Read-only: the replay does not patch any runtime module. It
reuses ``LogicalAuditor``, ``PremiseExtractor``,
``FrameDetector``, ``FrameTensionLayer``, ``FrameTensionRouter``
and (only for the ``frame_strategy_origin`` field) the v4.1
strategy callables.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import ExternalChain
from ..external_probe.enums import Domain, GroundTruth
from ..frame_inference import InferenceStrategy
from ..frame_inference.strategies import (
    f4_context_window, is_context_strategy, stateless_strategy,
)
from ..frame_tension import FrameTensionLayer
from ..frame_tension_integration import (
    FrameRoutingLedgerEvent, FrameTensionRouter,
)
from ..frames import FrameDetector, FrameKind
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from ..logic.premises import PremiseExtractor
from .cases import FalseSupportCase


@dataclass(frozen=True)
class ReplayRecord:
    chain_id: str
    domain: str
    frame_kind: str
    routing_decision: str
    support_state: str
    suspension_markers: tuple[str, ...]
    matched_premises: tuple[str, ...]
    extracted_links: tuple[str, ...]
    conclusion_tokens: tuple[str, ...]
    frame_strategy_origin: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "frame_kind": self.frame_kind,
            "routing_decision": self.routing_decision,
            "support_state": self.support_state,
            "suspension_markers": list(self.suspension_markers),
            "matched_premises": list(self.matched_premises),
            "extracted_links": list(self.extracted_links),
            "conclusion_tokens": list(self.conclusion_tokens),
            "frame_strategy_origin":
                list(self.frame_strategy_origin),
        }


_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were",
    "of", "to", "in", "on", "at", "and", "or", "for",
    "with", "by", "from", "as", "be", "been",
    "this", "that", "these", "those", "it",
    "therefore", "thus", "so", "hence",
})


def _content_tokens(text: str) -> tuple[str, ...]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    return tuple(sorted({
        t for t in s.split()
        if t not in _STOPWORDS and len(t) >= 3
    }))


def _suspension_markers_fired(text: str) -> tuple[str, ...]:
    """Surface markers known to the audit pipeline. We list the
    ones that would *suspend* if extended to cover this text.
    The list mirrors the markers the audit consults — we do not
    introduce any new marker buckets here.
    """
    fired: list[str] = []
    low = " " + text.lower() + " "
    # Hidden-negation surface tokens (the v3.16 set does NOT
    # cover these; their absence from the v3.16 list is the
    # reason the chain slips through).
    hidden_neg = (
        " rules out ", " ruled out ", " ruling out ",
        " is excluded ", " are excluded ", " excluded ",
        " is forgotten ", " forgotten ", " no measurable ",
        " no effect ", " no observable ",
        " is singular ", " are supplementary ",
        " diverges ", " no real ", " no limit ",
        " safely deferred ",
    )
    quant = (
        " guaranteed ", " single-handedly ", " alone ",
        " solely ", " sole ", " entire ", " only ",
        " unambiguously ", " conclusively ", " ever ",
        " never ", " every ", " all ",
        " single ", " any ",
    )
    auth = (
        " endorsed ", " endorse ", " validated ",
        " confirmed ", " asserted ", " asserts ",
        " established ", " approved ", " declared ",
        " certified ", " documented ", " reportedly ",
        " backed ", " backed by ",
    )
    metaphor = (
        " like a ", " like an ", " as if ", " as though ",
        " loosely speaking ", " in a sense ",
        " metaphorically ", " figuratively ",
    )
    tool = (
        " percent ", " % ", " degrees ", " milligrams ",
        " kilometres ", " miles ", " kilograms ",
    )
    for label, bucket in (
        ("HIDDEN_NEG", hidden_neg),
        ("QUANT", quant),
        ("AUTH", auth),
        ("METAPHOR", metaphor),
        ("TOOL", tool),
    ):
        for m in bucket:
            if m in low:
                fired.append(f"{label}:{m.strip()}")
    return tuple(sorted(set(fired)))


def _frame_strategy_origin(text: str) -> tuple[str, ...]:
    """Which v4.1 strategies would assign a non-null frame to
    this chain. The chain becomes ``false_support`` only when
    one of these strategies unlocks routing."""
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


def _extracted_links(
    premises: tuple, conclusion_text: str,
) -> tuple[str, ...]:
    """Token-link summary across the chain — the (premise_id,
    conclusion_token) pairs that *would* be the warrant if the
    rule had a real semantic content checker. Used purely for
    inspection; the v2.7 rule has no such checker.
    """
    concl = set(_content_tokens(conclusion_text))
    links: list[str] = []
    for i, p in enumerate(premises):
        ptoks = set(_content_tokens(p.text))
        shared = sorted(concl & ptoks)
        if shared:
            links.append(f"p{i}:" + ",".join(shared))
        else:
            links.append(f"p{i}:-")
    return tuple(links)


def replay_case(case: FalseSupportCase) -> ReplayRecord:
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
    route = router.route(
        claim_id=case.chain_id, claim_text=case.text,
        inherited_context_text="",
    )

    conclusion_text = (
        extracted.conclusion.text if extracted.conclusion else ""
    )
    return ReplayRecord(
        chain_id=case.chain_id, domain=case.domain,
        frame_kind=decl.frame_kind.value,
        routing_decision=route.event.value,
        support_state=audit.state.value,
        suspension_markers=_suspension_markers_fired(case.text),
        matched_premises=tuple(
            p.text for p in extracted.premises
        ),
        extracted_links=_extracted_links(
            extracted.premises, conclusion_text,
        ),
        conclusion_tokens=_content_tokens(conclusion_text),
        frame_strategy_origin=_frame_strategy_origin(case.text),
    )


def replay_all(
    cases: tuple[FalseSupportCase, ...],
) -> tuple[ReplayRecord, ...]:
    return tuple(replay_case(c) for c in cases)


__all__ = ["ReplayRecord", "replay_all", "replay_case"]
