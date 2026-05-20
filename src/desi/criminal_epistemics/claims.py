"""v16.0 - claim corpus for the Kennedy-
assassination epistemics sandbox.

CRITICAL HONESTY / SAFETY NOTES
===============================
1. This module structures PUBLICLY DOCUMENTED
   claims about a historical case (Warren
   Commission, HSCA, witness testimony, ballistics
   reports, public timelines, press). It makes NO
   new factual assertions. Every ``status`` below
   records the PUBLIC EVIDENTIARY STANDING of a
   claim (how well-attested or contested it is in
   the public record) - it is NOT DESi adjudicating
   historical truth.

2. DESi NEVER names a final perpetrator, NEVER
   declares the case "solved", NEVER confirms a
   conspiracy, NEVER presents speculation as fact,
   and NEVER claims historical authority. The
   closed status vocabulary contains no "guilty",
   "true", or "solved" value.

3. Speculative and unresolved claims are kept
   SPECULATIVE / UNRESOLVED by design. The point of
   the sandbox is to keep uncertainty visible, map
   conflicts, and resist escalation - not to pick a
   winning narrative.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimStatus(str, Enum):
    """Closed epistemic-standing vocabulary for a
    claim, ordered weakest-truth-pressure last."""
    VERIFIED = "VERIFIED"
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    PLAUSIBLE = "PLAUSIBLE"
    CONTESTED = "CONTESTED"
    SPECULATIVE = "SPECULATIVE"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


CLAIM_STATUSES: tuple[str, ...] = tuple(
    s.value for s in ClaimStatus
)

# Evidence-grade rank (how much the public record
# supports the claim). Used to detect escalation;
# REJECTED and UNRESOLVED sit outside the support
# ladder and are handled explicitly.
_EVIDENCE_RANK: dict[str, int] = {
    ClaimStatus.REJECTED.value: 0,
    ClaimStatus.UNRESOLVED.value: 1,
    ClaimStatus.SPECULATIVE.value: 2,
    ClaimStatus.CONTESTED.value: 3,
    ClaimStatus.PLAUSIBLE.value: 4,
    ClaimStatus.STRONGLY_SUPPORTED.value: 5,
    ClaimStatus.VERIFIED.value: 6,
}


def evidence_rank(status: str) -> int:
    return _EVIDENCE_RANK[status]


class Source(str, Enum):
    """Public source CATEGORIES. Each is treated as
    an independent line for topology purposes."""
    WARREN_COMMISSION = "warren_commission"
    HSCA = "hsca"
    WITNESS_TESTIMONY = "witness_testimony"
    BALLISTICS_REPORT = "ballistics_report"
    PUBLIC_TIMELINE = "public_timeline"
    PRESS_REPORT = "press_report"
    COMPETING_HYPOTHESIS = "competing_hypothesis"


SOURCES: tuple[str, ...] = tuple(
    s.value for s in Source
)

# Sources that are primary investigative / physical
# lines of evidence (independent corroboration);
# a competing hypothesis is NOT independent
# corroboration of itself.
_CORROBORATING = frozenset({
    Source.WARREN_COMMISSION.value,
    Source.HSCA.value,
    Source.WITNESS_TESTIMONY.value,
    Source.BALLISTICS_REPORT.value,
    Source.PUBLIC_TIMELINE.value,
    Source.PRESS_REPORT.value,
})


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    status: str
    sources: tuple[str, ...]
    # claims this one rests on (evidence lineage)
    depends_on: tuple[str, ...] = ()
    # the question this claim answers (for conflict
    # clustering), and its stance on that question
    topic: str = ""
    stance: str = ""
    # how strongly some narratives ASSERT the claim
    # (used to detect unsupported escalation); a
    # status value, defaults to the claim's own.
    asserted_as: str = ""
    # for REJECTED claims, the lines that reject it
    rejected_by: tuple[str, ...] = ()
    is_public_record_summary: bool = True

    def independence(self) -> int:
        """Number of distinct corroborating source
        categories (a competing hypothesis does not
        count as independent corroboration)."""
        return len(
            {s for s in self.sources}
            & _CORROBORATING
        )

    def asserted_status(self) -> str:
        return self.asserted_as or self.status

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "status": self.status,
            "sources": list(self.sources),
            "depends_on": list(self.depends_on),
            "topic": self.topic,
            "stance": self.stance,
            "asserted_as": self.asserted_status(),
            "rejected_by": list(self.rejected_by),
            "independence": self.independence(),
            "is_public_record_summary":
                self.is_public_record_summary,
        }


def _S(*xs: Source) -> tuple[str, ...]:
    return tuple(x.value for x in xs)


# Neutrally-worded encodings of publicly documented
# claims and their PUBLIC evidentiary standing. No
# perpetrator is named; no theory is endorsed.
_CLAIMS: tuple[Claim, ...] = (
    Claim(
        claim_id="C01",
        text=(
            "President John F. Kennedy was fatally "
            "shot in Dealey Plaza, Dallas, on 22 "
            "November 1963."
        ),
        status=ClaimStatus.VERIFIED.value,
        sources=_S(
            Source.WARREN_COMMISSION, Source.HSCA,
            Source.PUBLIC_TIMELINE,
            Source.PRESS_REPORT,
        ),
    ),
    Claim(
        claim_id="C02",
        text=(
            "Lee Harvey Oswald was arrested in "
            "Dallas on the day of the assassination."
        ),
        status=ClaimStatus.VERIFIED.value,
        sources=_S(
            Source.WARREN_COMMISSION, Source.HSCA,
            Source.PUBLIC_TIMELINE,
            Source.PRESS_REPORT,
        ),
    ),
    Claim(
        claim_id="C03",
        text=(
            "Lee Harvey Oswald was shot and killed "
            "by Jack Ruby on 24 November 1963."
        ),
        status=ClaimStatus.VERIFIED.value,
        sources=_S(
            Source.WARREN_COMMISSION,
            Source.PUBLIC_TIMELINE,
            Source.PRESS_REPORT,
        ),
    ),
    Claim(
        claim_id="C04",
        text=(
            "Texas Governor John Connally was "
            "wounded during the shooting."
        ),
        status=ClaimStatus.VERIFIED.value,
        sources=_S(
            Source.WARREN_COMMISSION, Source.HSCA,
            Source.PRESS_REPORT,
        ),
    ),
    Claim(
        claim_id="C05",
        text=(
            "Shots were fired at the motorcade from "
            "the Texas School Book Depository."
        ),
        status=ClaimStatus.STRONGLY_SUPPORTED.value,
        sources=_S(
            Source.WARREN_COMMISSION, Source.HSCA,
            Source.BALLISTICS_REPORT,
        ),
        depends_on=("C01",),
        topic="shot_origin", stance="depository",
    ),
    Claim(
        claim_id="C06",
        text=(
            "A rifle linked to Oswald was recovered "
            "on the sixth floor of the Depository."
        ),
        status=ClaimStatus.STRONGLY_SUPPORTED.value,
        sources=_S(
            Source.WARREN_COMMISSION, Source.HSCA,
            Source.BALLISTICS_REPORT,
        ),
    ),
    Claim(
        claim_id="C07",
        text=(
            "The wounds are explained by shots from "
            "a single shooter location."
        ),
        status=ClaimStatus.CONTESTED.value,
        sources=_S(
            Source.WARREN_COMMISSION,
            Source.BALLISTICS_REPORT,
        ),
        depends_on=("C05",),
        topic="shooter_count", stance="single",
    ),
    Claim(
        claim_id="C08",
        text=(
            "A single bullet accounts for the "
            "non-fatal wounds to Kennedy and "
            "Connally."
        ),
        status=ClaimStatus.CONTESTED.value,
        sources=_S(
            Source.WARREN_COMMISSION,
            Source.BALLISTICS_REPORT,
        ),
        depends_on=("C07",),
        topic="single_bullet", stance="single",
    ),
    Claim(
        claim_id="C09",
        text=(
            "Acoustic analysis was read as "
            "indicating a probable second shooter."
        ),
        status=ClaimStatus.CONTESTED.value,
        sources=_S(
            Source.HSCA,
            Source.COMPETING_HYPOTHESIS,
        ),
        topic="shooter_count", stance="multiple",
    ),
    Claim(
        claim_id="C10",
        text=(
            "A 1979 review concluded the "
            "assassination probably involved more "
            "than one participant, without "
            "identifying any."
        ),
        status=ClaimStatus.CONTESTED.value,
        sources=_S(Source.HSCA),
        topic="participants", stance="multiple",
    ),
    Claim(
        claim_id="C11",
        text=(
            "A specific named organization directed "
            "the assassination."
        ),
        status=ClaimStatus.SPECULATIVE.value,
        sources=_S(Source.COMPETING_HYPOTHESIS),
        topic="participants", stance="organized",
        # some narratives push this far past its
        # evidence - the escalation detector flags it
        asserted_as=ClaimStatus.VERIFIED.value,
    ),
    Claim(
        claim_id="C12",
        text=(
            "Oswald had no connection to the rifle "
            "recovered in the Depository."
        ),
        status=ClaimStatus.REJECTED.value,
        sources=_S(Source.COMPETING_HYPOTHESIS),
        rejected_by=_S(
            Source.BALLISTICS_REPORT,
            Source.WARREN_COMMISSION,
        ),
    ),
    Claim(
        claim_id="C13",
        text=(
            "Oswald's complete motive is fully "
            "established."
        ),
        status=ClaimStatus.UNRESOLVED.value,
        sources=_S(Source.WARREN_COMMISSION),
    ),
    Claim(
        claim_id="C14",
        text=(
            "Some witnesses perceived shots as "
            "coming from the grassy-knoll area."
        ),
        status=ClaimStatus.PLAUSIBLE.value,
        sources=_S(Source.WITNESS_TESTIMONY),
        topic="shot_origin", stance="knoll",
    ),
    Claim(
        claim_id="C15",
        text=(
            "Most surveyed witnesses associated the "
            "shots with the Depository direction."
        ),
        status=ClaimStatus.STRONGLY_SUPPORTED.value,
        sources=_S(
            Source.WITNESS_TESTIMONY, Source.HSCA,
        ),
        topic="shot_origin", stance="depository",
    ),
    Claim(
        claim_id="C16",
        text=(
            "Every individual with possible "
            "foreknowledge has been identified."
        ),
        status=ClaimStatus.UNRESOLVED.value,
        sources=_S(),
    ),
)


def claims() -> tuple[Claim, ...]:
    return _CLAIMS


def by_id(claim_id: str) -> Claim:
    for c in _CLAIMS:
        if c.claim_id == claim_id:
            return c
    raise KeyError(claim_id)


def claim_ids() -> tuple[str, ...]:
    return tuple(c.claim_id for c in _CLAIMS)


def topics() -> tuple[str, ...]:
    seen: list[str] = []
    for c in _CLAIMS:
        if c.topic and c.topic not in seen:
            seen.append(c.topic)
    return tuple(seen)


__all__ = [
    "CLAIM_STATUSES",
    "SOURCES",
    "Claim",
    "ClaimStatus",
    "Source",
    "by_id",
    "claim_ids",
    "claims",
    "evidence_rank",
    "topics",
]
