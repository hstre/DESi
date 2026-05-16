"""Aufgaben 6 + 7 — five counterfactual content probes.

Each probe is a *simulation*. It defines a deterministic
``triggers(text, record)`` predicate that answers
``would this probe block the chain?`` for one residue case.
No runtime patch.
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
from .classifier import (
    _DIRECT_CONTRADICTION_PAIRS,
    _INVERSION_PAIRS,
    _NECESSARY_SUFFICIENT_PAIRS,
    _POLARITY_REVERSAL_PAIRS,
    _has_pair, _normalised,
)
from .enums import ContentProbe


_STOPWORDS_FOR_ENTITY: frozenset[str] = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "of", "to", "in", "on", "at", "and", "or", "for",
    "with", "by", "from", "as", "be", "been", "is",
    "are", "was", "were", "it", "they", "we", "he",
    "she", "him", "her", "their", "its",
    "therefore", "thus", "so", "hence", "than", "more",
    "less", "very", "much", "many", "any",
})


# --- C1 contradiction_pair_check ----------------------------

def _c1_contradiction_pair_check(text: str) -> bool:
    return _has_pair(text, _DIRECT_CONTRADICTION_PAIRS)


# --- C2 polarity_flip_check ---------------------------------

def _c2_polarity_flip_check(text: str) -> bool:
    return _has_pair(text, _POLARITY_REVERSAL_PAIRS)


# --- C3 cause_direction_check -------------------------------

def _c3_cause_direction_check(text: str) -> bool:
    return _has_pair(text, _INVERSION_PAIRS)


# --- C4 necessity_sufficiency_check -------------------------

def _c4_necessity_sufficiency_check(text: str) -> bool:
    return _has_pair(text, _NECESSARY_SUFFICIENT_PAIRS)


# --- C5 entity_consistency_check ----------------------------

def _content_words(text: str) -> set[str]:
    """Content tokens for entity-overlap checks."""
    s = _normalised(text)
    out: set[str] = set()
    for tok in s.split():
        if tok in _STOPWORDS_FOR_ENTITY:
            continue
        if len(tok) < 3:
            continue
        out.add(tok)
    return out


def _c5_entity_consistency_check(text: str) -> bool:
    """Fire when the conclusion contains a content token that
    does NOT appear in any premise (a new entity introduced
    by the conclusion without premise support)."""
    extractor = PremiseExtractor()
    e = extractor.extract(text)
    if e.conclusion is None or not e.premises:
        return False
    concl = _content_words(e.conclusion.text)
    premise_union = set()
    for p in e.premises:
        premise_union |= _content_words(p.text)
    novel = concl - premise_union
    return len(novel) >= 1


_PREDICATES = {
    ContentProbe.C1_CONTRADICTION_PAIR_CHECK:
        _c1_contradiction_pair_check,
    ContentProbe.C2_POLARITY_FLIP_CHECK:
        _c2_polarity_flip_check,
    ContentProbe.C3_CAUSE_DIRECTION_CHECK:
        _c3_cause_direction_check,
    ContentProbe.C4_NECESSITY_SUFFICIENCY_CHECK:
        _c4_necessity_sufficiency_check,
    ContentProbe.C5_ENTITY_CONSISTENCY_CHECK:
        _c5_entity_consistency_check,
}


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
    case: ResidueCase, probe: ContentProbe,
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
    for probe in ContentProbe:
        for case in cases:
            out.append(evaluate_case(case, probe))
    return tuple(out)


def _protected_valid_texts() -> tuple[str, ...]:
    """Pool of every VALID-labeled chain across protected
    benchmarks. We do *not* pre-filter by current audit state
    — contamination = the predicate firing on any VALID chain
    is a candidate regression."""
    pool: list[str] = []
    for case in MAIN_CASES:
        pool.append(case.text)
    for case in ALL_MULTISTEP_CASES:
        pool.append(case.text)
    for case in ALL_HELDOUT_CASES:
        pool.append(case.text)
    for case in all_chains():
        if case.ground_truth is GroundTruth.VALID:
            pool.append(case.text)
    return tuple(pool)


__all__ = [
    "ProbeCaseOutcome", "evaluate_all", "evaluate_case",
    "_protected_valid_texts",
]
