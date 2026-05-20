"""Aufgaben 6 + 7 — five counterfactual warrant probes.

Each probe defines a deterministic ``triggers(text, record)``
predicate answering *would this probe block the chain?* for
one residue case. No runtime patch; we only measure what the
probe *would* do if active.

For every probe we then count:

* rescued_cases    — residue cases the probe blocks
* rescue_rate      — rescued / total
* false_blocks     — protected VALID chains the probe would
                     also block (contamination_risk synonym)

A probe with ``contamination_risk > 0`` is ``UNSAFE``.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..external_probe.corpus import all_chains
from ..external_probe.enums import GroundTruth
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.premises import PremiseExtractor
from .cases import ResidueCase
from .enums import WarrantProbe


# ---------- surface marker buckets used by probes -------------

_BRIDGE_RULE_HINTS: tuple[str, ...] = (
    " every ", " every patient ", " every cohort ",
    " all ", " any ", " if and only if ", " therefore ",
    " by definition ", " by the theorem ",
    " by the rule ", " by the principle ", " by the statute ",
    " under the statute ", " under the act ",
    " according to ", " every prime ", " every interval ",
)

_UNIVERSAL_QUANTIFIER_HINTS: tuple[str, ...] = (
    " a person's ", " an individual's ",
    " across every ", " for every ",
    " in every ", " across all ",
    " any patient ", " any cohort ",
    " any future ", " any scenario ",
    " a lifetime ", " for life ",
)

_MODALITY_PAST_MARKERS: tuple[str, ...] = (
    " showed ", " logged ", " reported ", " noted ",
    " appeared ", " observed ", " confirmed ",
    " tracked ", " filed ", " was ", " were ",
    " had ", " did ",
)

_MODALITY_FUTURE_MARKERS: tuple[str, ...] = (
    " will ", " must ", " cannot ", " should ", " would ",
)

_EXCEPTION_HINTS: tuple[str, ...] = (
    " unless ", " except ", " however ", " but ",
    " provided that ", " in cases where ",
    " when controlled for ", " assuming ",
)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    padded = _normalised(text)
    return any(m in padded for m in markers)


def _conclusion_overlap_ratio(text: str) -> float:
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return 0.0
    concl_toks = set(_tokens(e.conclusion.text))
    if not concl_toks:
        return 0.0
    for p in e.premises:
        ptoks = set(_tokens(p.text))
        ratio = len(concl_toks & ptoks) / len(concl_toks)
        if ratio >= 0.8:
            return ratio
    return 0.0


def _tokens(text: str) -> set[str]:
    s = _normalised(text)
    return {
        t for t in s.split()
        if len(t) >= 3
        and t not in {"the", "and", "for", "with",
                      "that", "from"}
    }


# ---------- W1 explicit_bridge_required ----------------------

def _w1_explicit_bridge_required(text: str) -> bool:
    """Suspend when no premise carries an explicit bridge-rule
    marker (universal quantifier / statute citation /
    theorem invocation). Most natural prose lacks such
    markers, so the probe is expected to be aggressive."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    for p in e.premises:
        if _contains_any(p.text, _BRIDGE_RULE_HINTS):
            return False
    return True


# ---------- W2 universal_quantifier_guard --------------------

def _w2_universal_quantifier_guard(text: str) -> bool:
    """Suspend when the conclusion uses a universal-shaped
    referent (`a person's`, `for every ...`, etc.) that the
    premises do not explicitly establish."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    if not _contains_any(
            e.conclusion.text, _UNIVERSAL_QUANTIFIER_HINTS,
    ):
        return False
    # Allow if a premise carries the same universal hint.
    for p in e.premises:
        if _contains_any(p.text, _UNIVERSAL_QUANTIFIER_HINTS):
            return False
    return True


# ---------- W3 modality_consistency_check --------------------

def _w3_modality_consistency_check(text: str) -> bool:
    """Suspend when at least one premise is observational/past
    and the conclusion uses a modal/future verb that no
    premise itself introduced."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    if not _contains_any(
            e.conclusion.text, _MODALITY_FUTURE_MARKERS,
    ):
        return False
    any_past = any(
        _contains_any(p.text, _MODALITY_PAST_MARKERS)
        for p in e.premises
    )
    if not any_past:
        return False
    for p in e.premises:
        if _contains_any(p.text, _MODALITY_FUTURE_MARKERS):
            return False
    return True


# ---------- W4 exception_trace_required ----------------------

def _w4_exception_trace_required(text: str) -> bool:
    """Suspend when the chain makes a categorical claim
    (conclusion contains 'is' / 'are' / 'will' etc.) without
    any exception qualifier appearing in any premise."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    # Categorical-conclusion heuristic — every v4.6 conclusion
    # is a copula-style claim ('is X', 'will Y', 'cannot Z').
    categorical = (
        " is " in _normalised(e.conclusion.text)
        or " are " in _normalised(e.conclusion.text)
        or _contains_any(
            e.conclusion.text, _MODALITY_FUTURE_MARKERS,
        )
    )
    if not categorical:
        return False
    for p in e.premises:
        if _contains_any(p.text, _EXCEPTION_HINTS):
            return False
    if _contains_any(e.conclusion.text, _EXCEPTION_HINTS):
        return False
    return True


# ---------- W5 premise_conclusion_nonidentity ---------------

def _w5_premise_conclusion_nonidentity(text: str) -> bool:
    """Suspend when conclusion is a token-level paraphrase of
    a single premise (>= 80% conclusion-token coverage by one
    premise)."""
    return _conclusion_overlap_ratio(text) >= 0.8


_PREDICATES = {
    WarrantProbe.W1_EXPLICIT_BRIDGE_REQUIRED:
        _w1_explicit_bridge_required,
    WarrantProbe.W2_UNIVERSAL_QUANTIFIER_GUARD:
        _w2_universal_quantifier_guard,
    WarrantProbe.W3_MODALITY_CONSISTENCY_CHECK:
        _w3_modality_consistency_check,
    WarrantProbe.W4_EXCEPTION_TRACE_REQUIRED:
        _w4_exception_trace_required,
    WarrantProbe.W5_PREMISE_CONCLUSION_NONIDENTITY:
        _w5_premise_conclusion_nonidentity,
}


# ---------- per-case probe outcome --------------------------

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
    case: ResidueCase, probe: WarrantProbe,
) -> ProbeCaseOutcome:
    blocks = _PREDICATES[probe](case.text)
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
    for probe in WarrantProbe:
        for case in cases:
            out.append(evaluate_case(case, probe))
    return tuple(out)


# ---------- contamination pool -------------------------------

def _protected_valid_texts() -> tuple[str, ...]:
    auditor = LogicalAuditor()
    pool: list[str] = []
    for c in MAIN_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            pool.append(c.text)
    for c in ALL_MULTISTEP_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            pool.append(c.text)
    for c in ALL_HELDOUT_CASES:
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            pool.append(c.text)
    for c in all_chains():
        if c.ground_truth is not GroundTruth.VALID:
            continue
        a = auditor.audit(c.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            pool.append(c.text)
    return tuple(pool)


__all__ = [
    "ProbeCaseOutcome", "evaluate_all", "evaluate_case",
    "_protected_valid_texts",
]
