"""Aufgabe 9 — contamination check against every DESi corpus.

Every external chain text is compared against every DESi
corpus text the audit has access to. An exact substring or
high-jaccard match fails the check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_naturalness.negative_control import (
    ALL_NC_CHAINS as V318_NCS,
)
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_invariance import ALL_GROUPS as INV_GROUPS
from ..heldout_causal import ALL_HELDOUT_CASES
from ..tools.benchmark import ALL_TOOL_CASES
from .corpus import ExternalChain


_STOPWORDS = frozenset({
    "the", "a", "an", "this", "that", "is", "are", "was", "were",
    "of", "in", "on", "at", "to", "for", "with", "and", "or",
    "therefore", "thus", "so", "if", "while", "when", "where",
})


def _tokens(text: str) -> set[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    return {
        t for t in s.split()
        if t not in _STOPWORDS and len(t) >= 3
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _desi_texts() -> tuple[str, ...]:
    out: list[str] = []
    out.extend(c.text for c in MAIN_CASES)
    out.extend(c.text for c in ALL_MULTISTEP_CASES)
    out.extend(c.text for c in ALL_FRAME_CASES)
    for g in INV_GROUPS:
        out.append(g.canonical_text)
        out.extend(g.paraphrases)
    out.extend(c.text for c in ALL_TOOL_CASES)
    out.extend(c.text for c in ALL_ADVERSARIAL_CASES)
    out.extend(c.text for c in ALL_HELDOUT_CASES)
    out.extend(c.text for c in V318_NCS)
    return tuple(out)


SEMANTIC_OVERLAP_THRESHOLD: float = 0.20


@dataclass(frozen=True)
class ContaminationHit:
    chain_id: str
    domain: str
    desi_text_excerpt: str
    overlap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "desi_text_excerpt": self.desi_text_excerpt[:60],
            "overlap": self.overlap,
        }


@dataclass(frozen=True)
class ContaminationReport:
    checked_count: int
    desi_corpus_count: int
    exact_overlap_count: int
    semantic_overlap_count: int
    hits: tuple[ContaminationHit, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "checked_count": self.checked_count,
            "desi_corpus_count": self.desi_corpus_count,
            "exact_overlap_count": self.exact_overlap_count,
            "semantic_overlap_count": self.semantic_overlap_count,
            "hits": [h.to_dict() for h in self.hits],
        }


def check(chains: Iterable[ExternalChain]) -> ContaminationReport:
    desi = _desi_texts()
    desi_set = set(desi)
    desi_tokens = [(_tokens(t), t) for t in desi]
    hits: list[ContaminationHit] = []
    exact = 0
    semantic = 0
    n = 0
    for c in chains:
        n += 1
        if c.text in desi_set:
            exact += 1
            hits.append(ContaminationHit(
                chain_id=c.chain_id, domain=c.domain.value,
                desi_text_excerpt=c.text, overlap=1.0,
            ))
            continue
        ct = _tokens(c.text)
        best_overlap = 0.0
        best_text = ""
        for dt, dtext in desi_tokens:
            j = _jaccard(ct, dt)
            if j > best_overlap:
                best_overlap = j
                best_text = dtext
        if best_overlap > SEMANTIC_OVERLAP_THRESHOLD:
            semantic += 1
            hits.append(ContaminationHit(
                chain_id=c.chain_id, domain=c.domain.value,
                desi_text_excerpt=best_text,
                overlap=round(best_overlap, 6),
            ))
    return ContaminationReport(
        checked_count=n,
        desi_corpus_count=len(desi),
        exact_overlap_count=exact,
        semantic_overlap_count=semantic,
        hits=tuple(hits),
    )


__all__ = [
    "ContaminationHit",
    "ContaminationReport",
    "SEMANTIC_OVERLAP_THRESHOLD",
    "check",
]
