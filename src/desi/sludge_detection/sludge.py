"""v13.1 — sludge classification + detection.

DESi flags a paper as SLUDGE iff it has BOTH
of the structural sludge markers:

* hallucinated diagram
* hallucinated statistics

OR if it lacks BOTH method support AND
references_grounded AND has an overclaim.

The detector deliberately does NOT use writing
style. Same prose from a human or AI exits with
the same verdict. The directive's invariant:
no false accusation against BORDERLINE
(AI-assisted but legitimate) papers.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..paper_integrity.claims import (
    PaperClaim, PaperClass, fixture,
)


class SludgeVerdict(str, Enum):
    CLEAN     = "clean"
    SUSPECT   = "suspect"
    SLUDGE    = "sludge"


SLUDGE_VERDICTS: tuple[str, ...] = tuple(
    s.value for s in SludgeVerdict
)


def classify_sludge(
    p: PaperClaim,
) -> SludgeVerdict:
    if (
        p.has_hallucinated_diagram
        and p.has_hallucinated_stats
    ):
        return SludgeVerdict.SLUDGE
    if (
        not p.method_supported
        and not p.references_grounded
        and p.has_overclaim
    ):
        return SludgeVerdict.SLUDGE
    if p.has_overclaim and (
        not p.evidence_supported
    ):
        return SludgeVerdict.SUSPECT
    return SludgeVerdict.CLEAN


@dataclass(frozen=True)
class ClassifiedPaper:
    paper_id: str
    paper_class: str
    verdict: str
    is_actually_sludge: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "paper_class": self.paper_class,
            "verdict": self.verdict,
            "is_actually_sludge":
                self.is_actually_sludge,
        }


@lru_cache(maxsize=1)
def classified_papers() -> tuple[
    ClassifiedPaper, ...,
]:
    return tuple(
        ClassifiedPaper(
            paper_id=p.paper_id,
            paper_class=p.paper_class,
            verdict=classify_sludge(p).value,
            is_actually_sludge=(
                p.paper_class == (
                    PaperClass.AI_SLUDGE.value
                )
            ),
        )
        for p in fixture()
    )


def fake_paper_recall() -> float:
    """Recall on the AI_SLUDGE class - every
    actual sludge paper must be flagged as
    SLUDGE."""
    rows = classified_papers()
    target = [
        r for r in rows
        if r.is_actually_sludge
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target
        if r.verdict == (
            SludgeVerdict.SLUDGE.value
        )
    )
    return round(hit / len(target), 6)


def false_accusation_rate() -> float:
    """Fraction of non-SLUDGE papers (GOLD,
    WEAK, BORDERLINE, ADVERSARIAL) that DESi
    flagged as SLUDGE. Critical for the
    directive: BORDERLINE papers MUST NOT be
    accused. ADVERSARIAL papers may be flagged
    as SUSPECT (which is correct), but flagging
    them as SLUDGE only happens if their
    structure is sludge-shaped - which v13.0
    fixture deliberately keeps separate from
    AI_SLUDGE."""
    rows = classified_papers()
    if not rows:
        return 0.0
    bad = sum(
        1 for r in rows
        if (not r.is_actually_sludge)
        and r.verdict == (
            SludgeVerdict.SLUDGE.value
        )
    )
    return round(bad / len(rows), 6)


__all__ = [
    "ClassifiedPaper",
    "SLUDGE_VERDICTS",
    "SludgeVerdict",
    "classified_papers",
    "classify_sludge",
    "fake_paper_recall",
    "false_accusation_rate",
]
