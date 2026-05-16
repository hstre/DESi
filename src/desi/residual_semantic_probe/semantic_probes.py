"""Aufgaben 6 + 7 — five counterfactual semantic probes.

Each probe is a *simulation*. It defines a deterministic
``triggers(text, record)`` predicate that answers
``would this probe block the chain?`` for one residue case.
No runtime module is patched; we only measure what the probe
*would* do if it were active.

For every probe we then count:

* rescued_cases   — residue cases where the probe blocks
* rescue_rate     — rescued / total
* false_blocks    — protected VALID chains the probe would
                    also block (contamination_risk synonym)

Per directive Aufgabe 7: any probe with
``contamination_risk > 0`` is marked ``UNSAFE`` and excluded
from the rescue-localisation analysis.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..external_probe.corpus import all_chains
from ..external_probe.enums import GroundTruth
from ..frames import FrameDetector, FrameKind
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import (
    InferenceRule, _has_number_word,
)
from ..logic.premises import PremiseExtractor
from .cases import ResidueCase
from .enums import SemanticProbe
from .replay import ReplayRecord, _content_tokens


# ---------- shared text-feature helpers ----------------------

def _frame_kind(text: str) -> str:
    return FrameDetector().detect(
        claim_id="probe", source_text=text,
    ).frame_kind.value


def _overlap_signature(text: str) -> tuple[int, int]:
    """(overlap_premises, overlap_total) for any text — used
    when evaluating probes against benchmark chains that
    haven't been replayed by the v4.4 pipeline."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return 0, 0
    concl = set(_content_tokens(e.conclusion.text))
    overlap_premises = 0
    overlap_total = 0
    for p in e.premises:
        shared = concl & set(_content_tokens(p.text))
        if shared:
            overlap_premises += 1
            overlap_total += len(shared)
    return overlap_premises, overlap_total


# ---------- predicate definitions ----------------------------

def _s1_frame_tension_strict(text: str) -> bool:
    """Block when the detector cannot resolve an explicit
    frame from the text alone."""
    return _frame_kind(text) == FrameKind.FRAME_UNDECLARED.value


def _s2_inner_only_route(text: str) -> bool:
    """Block when there is no inner-side explicit ``Frame:``
    marker. The inner side is the chain text itself; an
    explicit marker would be detected as
    ``DetectionMethod.EXPLICIT_MARKER``. Under
    ``inner_only_route`` semantics, an unmarked chain has no
    proof of frame and cannot route."""
    return "frame:" not in text.lower()


def _s3_mandatory_consilium(text: str) -> bool:
    """Force every ``CAUSAL_CHAIN`` audit through consilium.
    Under the simulation, the audit's own SUPPORT verdict is
    not honoured; consilium would block.
    This predicate fires on every chain whose unmodified audit
    returns ``LOGICALLY_SUPPORTED`` under ``CAUSAL_CHAIN``."""
    auditor = LogicalAuditor()
    a = auditor.audit(text)
    return (
        a.state is LogicalState.LOGICALLY_SUPPORTED
        and a.rule is InferenceRule.CAUSAL_CHAIN
    )


def _s4_tool_gate_if_numeric(text: str) -> bool:
    """Route to tool gate if any premise or the conclusion
    contains a number word. The tool gate is not a
    ``CAUSAL_CHAIN`` audit; routing there blocks the
    causal verdict.
    """
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    if _has_number_word(e.conclusion.text):
        return True
    return any(_has_number_word(p.text) for p in e.premises)


def _s5_bidirectional_link_check(text: str) -> bool:
    """Detect the BIDIRECTIONAL_CYCLE shape: conclusion content
    tokens overlap with at least two distinct premises and
    total overlap is at least three tokens."""
    op, ot = _overlap_signature(text)
    return op >= 2 and ot >= 3


_PREDICATES = {
    SemanticProbe.S1_FRAME_TENSION_STRICT:    _s1_frame_tension_strict,
    SemanticProbe.S2_INNER_ONLY_ROUTE:        _s2_inner_only_route,
    SemanticProbe.S3_MANDATORY_CONSILIUM:     _s3_mandatory_consilium,
    SemanticProbe.S4_TOOL_GATE_IF_NUMERIC:    _s4_tool_gate_if_numeric,
    SemanticProbe.S5_BIDIRECTIONAL_LINK_CHECK:
        _s5_bidirectional_link_check,
}


# ---------- per-case probe outcome ---------------------------

@dataclass(frozen=True)
class ProbeCaseOutcome:
    chain_id: str
    probe: str
    would_block: bool
    would_allow: bool
    would_false_support: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "probe": self.probe,
            "would_block": self.would_block,
            "would_allow": self.would_allow,
            "would_false_support": self.would_false_support,
        }


def evaluate_case(
    case: ResidueCase, probe: SemanticProbe,
) -> ProbeCaseOutcome:
    pred = _PREDICATES[probe]
    blocks = pred(case.text)
    return ProbeCaseOutcome(
        chain_id=case.chain_id, probe=probe.value,
        would_block=blocks,
        would_allow=not blocks,
        would_false_support=(
            not blocks and case.ground_truth == "INVALID"
        ),
    )


def evaluate_all(
    cases: tuple[ResidueCase, ...],
) -> tuple[ProbeCaseOutcome, ...]:
    out: list[ProbeCaseOutcome] = []
    for probe in SemanticProbe:
        for case in cases:
            out.append(evaluate_case(case, probe))
    return tuple(out)


# ---------- contamination measurement ------------------------

def _protected_valid_texts() -> tuple[str, ...]:
    """Currently-audit-supported VALID-labeled chains across
    every protected benchmark. A probe that blocks any of
    these would cause a false-negative regression."""
    auditor = LogicalAuditor()
    out: list[str] = []
    for c in MAIN_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(c.text)
    for c in ALL_MULTISTEP_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(c.text)
    for c in ALL_HELDOUT_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(c.text)
    for c in all_chains():
        if c.ground_truth is not GroundTruth.VALID:
            continue
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(c.text)
    return tuple(out)


__all__ = [
    "ProbeCaseOutcome", "evaluate_all", "evaluate_case",
    "_protected_valid_texts",
]
