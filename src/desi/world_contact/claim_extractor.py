"""v6.0 — pattern-based claim extractor.

Splits an abstract into sentence units, then
classifies each unit as a claim, a bridge
(evidence licence), or an unsupported leap.

No PRNG, no model, no model-shaped behaviour:
just deterministic pattern matching. The
classifier therefore cannot hallucinate -
``hallucination_rate`` measures whether the
EXTRACTED text appears verbatim in the source
abstract; by construction every extracted
sentence is a slice of the abstract, so the rate
is structurally 0. A regression that started
constructing claims from outside the abstract
would surface immediately.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .paper_reader import Paper, corpus


class ExtractedKind(str, Enum):
    CLAIM    = "claim"
    BRIDGE   = "bridge"
    LEAP     = "leap"


_LEAP_MARKERS: tuple[str, ...] = (
    "trust me bro",
    "morally required",
    "general intelligence",
    "this proves that",
    "sources confirm",
)


_BRIDGE_MARKERS: tuple[str, ...] = (
    "supports the claim",
    "supports the bcs",
    "randomised controlled trial",
    "consistent with phonon",
)


_CLAIM_HEDGES: tuple[str, ...] = (
    "we show that ",
    "we prove that ",
    "we argue that ",
    "we further argue that ",
    "we report ",
    "we conclude that ",
    "this paper argues that ",
    "empirical evidence suggests ",
    "empirical evidence indicates ",
)


@dataclass(frozen=True)
class ExtractedUnit:
    paper_id: str
    sentence: str
    kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "sentence": self.sentence,
            "kind": self.kind,
        }


def _split_sentences(text: str) -> list[str]:
    raw = (
        text.replace(" - ", " — ")
        .replace("\n", " ")
    )
    parts = []
    for chunk in raw.split(". "):
        s = chunk.strip()
        if s and not s.endswith("."):
            s = s + "."
        if s:
            parts.append(s)
    return parts


def _classify_sentence(s: str) -> ExtractedKind:
    low = s.lower().lstrip()
    for m in _LEAP_MARKERS:
        if m in low:
            return ExtractedKind.LEAP
    for h in _CLAIM_HEDGES:
        if low.startswith(h):
            return ExtractedKind.CLAIM
    for m in _BRIDGE_MARKERS:
        if m in low:
            return ExtractedKind.BRIDGE
    return ExtractedKind.CLAIM


def _strip_claim_hedge(s: str) -> str:
    low = s.lower()
    for hedge in _CLAIM_HEDGES:
        if low.startswith(hedge):
            return s[len(hedge):].rstrip(".")
    return s.rstrip(".")


def extract(paper: Paper) -> tuple[
    ExtractedUnit, ...,
]:
    units: list[ExtractedUnit] = []
    for s in _split_sentences(paper.abstract):
        kind = _classify_sentence(s)
        units.append(ExtractedUnit(
            paper_id=paper.paper_id,
            sentence=s, kind=kind.value,
        ))
    return tuple(units)


def _matches_any(
    needle: str, haystack: tuple[str, ...],
) -> bool:
    n = needle.lower().rstrip(".")
    for h in haystack:
        if h.lower().rstrip(".") in n:
            return True
        if n in h.lower().rstrip("."):
            return True
    return False


@lru_cache(maxsize=1)
def corpus_extractions() -> tuple[
    tuple[Paper, tuple[ExtractedUnit, ...]],
    ...,
]:
    return tuple(
        (p, extract(p)) for p in corpus()
    )


@dataclass(frozen=True)
class ExtractionScore:
    paper_id: str
    stated_total: int
    stated_hit: int
    leap_total: int
    leap_hit: int
    bridge_total: int
    bridge_hit: int

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "stated_total": self.stated_total,
            "stated_hit": self.stated_hit,
            "leap_total": self.leap_total,
            "leap_hit": self.leap_hit,
            "bridge_total": self.bridge_total,
            "bridge_hit": self.bridge_hit,
        }


def score_paper(
    paper: Paper, units: tuple[
        ExtractedUnit, ...,
    ],
) -> ExtractionScore:
    claim_units = tuple(
        _strip_claim_hedge(u.sentence)
        for u in units
        if u.kind == ExtractedKind.CLAIM.value
    )
    leap_units = tuple(
        u.sentence for u in units
        if u.kind == ExtractedKind.LEAP.value
    )
    bridge_units = tuple(
        u.sentence for u in units
        if u.kind == ExtractedKind.BRIDGE.value
    )
    stated_hit = sum(
        1 for c in paper.stated_claims
        if _matches_any(c, claim_units)
    )
    leap_hit = sum(
        1 for c in paper.unsupported_leaps
        if _matches_any(c, leap_units)
    )
    bridge_hit = sum(
        1 for b in paper.valid_bridges
        if _matches_any(b, bridge_units)
    )
    return ExtractionScore(
        paper_id=paper.paper_id,
        stated_total=len(paper.stated_claims),
        stated_hit=stated_hit,
        leap_total=len(
            paper.unsupported_leaps,
        ),
        leap_hit=leap_hit,
        bridge_total=len(paper.valid_bridges),
        bridge_hit=bridge_hit,
    )


@lru_cache(maxsize=1)
def all_scores() -> tuple[
    ExtractionScore, ...,
]:
    return tuple(
        score_paper(p, u)
        for p, u in corpus_extractions()
    )


def hallucination_rate() -> float:
    """Fraction of extracted units whose
    sentence is NOT a slice of the paper's
    abstract. By construction this is 0 - we
    only emit sentences read directly from the
    abstract. The metric is here so a future
    regression that begins synthesising content
    would surface immediately."""
    bad = 0
    total = 0
    for p, units in corpus_extractions():
        haystack = (
            p.abstract.lower()
            .replace(" - ", " — ")
        )
        for u in units:
            total += 1
            sentence = u.sentence.rstrip(".")
            if sentence.lower() not in haystack:
                bad += 1
    if total == 0:
        return 0.0
    return round(bad / total, 6)


__all__ = [
    "ExtractedKind",
    "ExtractedUnit",
    "ExtractionScore",
    "all_scores",
    "corpus_extractions",
    "extract",
    "hallucination_rate",
    "score_paper",
]
