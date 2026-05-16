"""Aufgabe 1 — extract every adjacent link from every input corpus.

Each chain text is split into sentences; consecutive sentence
pairs become directed links. The decomposition is purely
text-based — no LogicalAuditor call, no PremiseExtractor — so
this module stays read-only and does not depend on the v2.7+
inference machinery.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .enums import CorpusSource


@dataclass(frozen=True)
class Link:
    chain_id: str
    corpus: CorpusSource
    index: int          # position within the chain (0-based)
    source_text: str
    target_text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "corpus": self.corpus.value,
            "index": self.index,
            "source_text": self.source_text,
            "target_text": self.target_text,
        }


def _sentences(text: str) -> tuple[str, ...]:
    """Split a chain text into ordered sentence fragments.

    "A. B. C. Therefore D." → ("A", "B", "C", "D")
    """
    # Normalise the "Therefore" connector so the conclusion sits
    # next to the last premise as a plain sentence.
    normalised = text.replace("Therefore ", "")
    parts = [s.strip() for s in normalised.split(".")]
    return tuple(p for p in parts if p)


def _links_for(
    chain_id: str, text: str, corpus: CorpusSource,
) -> tuple[Link, ...]:
    sents = _sentences(text)
    out: list[Link] = []
    for i in range(len(sents) - 1):
        out.append(Link(
            chain_id=chain_id, corpus=corpus, index=i,
            source_text=sents[i], target_text=sents[i + 1],
        ))
    return tuple(out)


def _v23_links() -> tuple[Link, ...]:
    out: list[Link] = []
    for case in ALL_MULTISTEP_CASES:
        out.extend(_links_for(
            chain_id=case.case_id, text=case.text,
            corpus=CorpusSource.V23_MULTISTEP,
        ))
    return tuple(out)


def _v314_links() -> tuple[Link, ...]:
    out: list[Link] = []
    for case in ALL_HELDOUT_CASES:
        out.extend(_links_for(
            chain_id=case.case_id, text=case.text,
            corpus=CorpusSource.V314_HELDOUT,
        ))
    return tuple(out)


def _v315_links() -> tuple[Link, ...]:
    out: list[Link] = []
    for case in ALL_ADVERSARIAL_CASES:
        out.extend(_links_for(
            chain_id=case.case_id, text=case.text,
            corpus=CorpusSource.V315_ADVERSARIAL,
        ))
    return tuple(out)


def _v316_suspended_links() -> tuple[Link, ...]:
    """v3.16-suspended subset: every v3.15 case that the patched
    CAUSAL_CHAIN now blocks. Determined live against the patched
    rule rather than pinned, so the module reflects the current
    runtime."""
    auditor = LogicalAuditor()
    out: list[Link] = []
    for case in ALL_ADVERSARIAL_CASES:
        r = auditor.audit(case.text)
        still_supported = (
            r.state == LogicalState.LOGICALLY_SUPPORTED
            and r.rule is InferenceRule.CAUSAL_CHAIN
        )
        if still_supported:
            continue
        out.extend(_links_for(
            chain_id=case.case_id, text=case.text,
            corpus=CorpusSource.V316_SUSPENDED,
        ))
    return tuple(out)


def extract_all_links() -> tuple[Link, ...]:
    return (
        _v23_links()
        + _v314_links()
        + _v315_links()
        + _v316_suspended_links()
    )


def per_corpus_links() -> dict[str, tuple[Link, ...]]:
    return {
        CorpusSource.V23_MULTISTEP.value:   _v23_links(),
        CorpusSource.V314_HELDOUT.value:    _v314_links(),
        CorpusSource.V315_ADVERSARIAL.value: _v315_links(),
        CorpusSource.V316_SUSPENDED.value:  _v316_suspended_links(),
    }


__all__ = [
    "Link",
    "extract_all_links",
    "per_corpus_links",
]
