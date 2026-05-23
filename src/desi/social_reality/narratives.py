"""v7.0 — synthetic narrative-pressure fixture.

The directive forbids live social media. The
fixture is a closed set of synthetic
narrative-shaped claims, each carrying a closed
ground-truth (narrative_kind, oversimplification,
emotional_charge, identity_appeal) tuple. The
detector is graded against that ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NarrativeKind(str, Enum):
    NEUTRAL_REPORT         = "neutral_report"
    EMOTIONAL_FRAME        = "emotional_frame"
    MORAL_OVERSIMPLIFY     = (
        "moral_oversimplify"
    )
    IDENTITY_APPEAL        = "identity_appeal"
    SIMPLE_CAUSAL_LEAP     = (
        "simple_causal_leap"
    )
    POPULAR_BUT_WEAK       = "popular_but_weak"


NARRATIVE_KINDS: tuple[str, ...] = tuple(
    k.value for k in NarrativeKind
)


@dataclass(frozen=True)
class NarrativeClaim:
    claim_id: str
    text: str
    narrative_kind: str
    emotional_charge: float
    oversimplification: float
    identity_appeal: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "narrative_kind":
                self.narrative_kind,
            "emotional_charge":
                self.emotional_charge,
            "oversimplification":
                self.oversimplification,
            "identity_appeal":
                self.identity_appeal,
        }


_FIXTURE: tuple[NarrativeClaim, ...] = (
    NarrativeClaim(
        claim_id="nar-001",
        text=(
            "Researchers report a 4 percent "
            "reduction in cardiovascular events "
            "in the trial cohort."
        ),
        narrative_kind=(
            NarrativeKind.NEUTRAL_REPORT.value
        ),
        emotional_charge=0.05,
        oversimplification=0.05,
        identity_appeal=0.0,
    ),
    NarrativeClaim(
        claim_id="nar-002",
        text=(
            "Children are DYING because the "
            "elites refuse to act."
        ),
        narrative_kind=(
            NarrativeKind.EMOTIONAL_FRAME.value
        ),
        emotional_charge=0.95,
        oversimplification=0.80,
        identity_appeal=0.60,
    ),
    NarrativeClaim(
        claim_id="nar-003",
        text=(
            "Either you support the policy or "
            "you support the suffering."
        ),
        narrative_kind=(
            NarrativeKind.MORAL_OVERSIMPLIFY
            .value
        ),
        emotional_charge=0.80,
        oversimplification=0.90,
        identity_appeal=0.50,
    ),
    NarrativeClaim(
        claim_id="nar-004",
        text=(
            "WE the truly informed know that "
            "THEY are hiding the data."
        ),
        narrative_kind=(
            NarrativeKind.IDENTITY_APPEAL.value
        ),
        emotional_charge=0.70,
        oversimplification=0.65,
        identity_appeal=0.95,
    ),
    NarrativeClaim(
        claim_id="nar-005",
        text=(
            "Vaccine uptake fell, therefore "
            "the mandate caused the decline."
        ),
        narrative_kind=(
            NarrativeKind.SIMPLE_CAUSAL_LEAP
            .value
        ),
        emotional_charge=0.30,
        oversimplification=0.90,
        identity_appeal=0.20,
    ),
    NarrativeClaim(
        claim_id="nar-006",
        text=(
            "Everyone knows that diet X is "
            "the only way to be healthy."
        ),
        narrative_kind=(
            NarrativeKind.POPULAR_BUT_WEAK
            .value
        ),
        emotional_charge=0.45,
        oversimplification=0.85,
        identity_appeal=0.40,
    ),
    NarrativeClaim(
        claim_id="nar-007",
        text=(
            "Meta-analysis finds a small effect "
            "with wide confidence intervals."
        ),
        narrative_kind=(
            NarrativeKind.NEUTRAL_REPORT.value
        ),
        emotional_charge=0.05,
        oversimplification=0.05,
        identity_appeal=0.0,
    ),
    NarrativeClaim(
        claim_id="nar-008",
        text=(
            "THEIR experts are corrupt. OUR "
            "experts are honest."
        ),
        narrative_kind=(
            NarrativeKind.IDENTITY_APPEAL.value
        ),
        emotional_charge=0.85,
        oversimplification=0.75,
        identity_appeal=0.95,
    ),
    NarrativeClaim(
        claim_id="nar-009",
        text=(
            "If you really cared about people "
            "you would agree."
        ),
        narrative_kind=(
            NarrativeKind.MORAL_OVERSIMPLIFY
            .value
        ),
        emotional_charge=0.80,
        oversimplification=0.85,
        identity_appeal=0.55,
    ),
    NarrativeClaim(
        claim_id="nar-010",
        text=(
            "A randomised trial estimates a "
            "12 percent reduction with p<0.05."
        ),
        narrative_kind=(
            NarrativeKind.NEUTRAL_REPORT.value
        ),
        emotional_charge=0.05,
        oversimplification=0.10,
        identity_appeal=0.0,
    ),
    NarrativeClaim(
        claim_id="nar-011",
        text=(
            "Crime spiked, and immigration "
            "rose, so immigration causes crime."
        ),
        narrative_kind=(
            NarrativeKind.SIMPLE_CAUSAL_LEAP
            .value
        ),
        emotional_charge=0.55,
        oversimplification=0.90,
        identity_appeal=0.40,
    ),
    NarrativeClaim(
        claim_id="nar-012",
        text=(
            "Millions agree that the solution "
            "is obvious."
        ),
        narrative_kind=(
            NarrativeKind.POPULAR_BUT_WEAK
            .value
        ),
        emotional_charge=0.40,
        oversimplification=0.80,
        identity_appeal=0.30,
    ),
)


def fixture() -> tuple[NarrativeClaim, ...]:
    return _FIXTURE


def narrative_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.narrative_kind for c in fixture()
    ))


__all__ = [
    "NARRATIVE_KINDS",
    "NarrativeClaim",
    "NarrativeKind",
    "fixture",
    "narrative_counts",
]
