"""v7.1 — closed epistemic-tribe taxonomy and
fixture.

Each tribal claim carries a closed
``EpistemicTribe`` label plus an INTRINSIC
``epistemic_quality`` score that is independent
of the tribe. The downstream classifier must
assign certainty based on epistemic_quality
alone, never on tribe identity - that is the
structural guarantee of neutrality.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EpistemicTribe(str, Enum):
    TRIBE_A_TECHNOCRATIC  = (
        "tribe_a_technocratic"
    )
    TRIBE_B_POPULIST      = (
        "tribe_b_populist"
    )
    TRIBE_C_TRADITIONAL   = (
        "tribe_c_traditional"
    )
    TRIBE_D_PROGRESSIVE   = (
        "tribe_d_progressive"
    )
    INDEPENDENT           = "independent"


EPISTEMIC_TRIBES: tuple[str, ...] = tuple(
    t.value for t in EpistemicTribe
)


@dataclass(frozen=True)
class TribalClaim:
    claim_id: str
    tribe: str
    text: str
    epistemic_quality: float
    is_evidence_backed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "tribe": self.tribe,
            "text": self.text,
            "epistemic_quality":
                self.epistemic_quality,
            "is_evidence_backed":
                self.is_evidence_backed,
        }


# Three claims per tribe x 5 tribes = 15.
# Each tribe carries a MIX of high-quality and
# low-quality claims so a fair classifier can
# distinguish quality independently of tribe.
_FIXTURE: tuple[TribalClaim, ...] = (
    TribalClaim(
        claim_id="t-a-001",
        tribe=(
            EpistemicTribe
            .TRIBE_A_TECHNOCRATIC.value
        ),
        text=(
            "RCT shows a 4 percent reduction "
            "in cardiovascular events."
        ),
        epistemic_quality=0.90,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-a-002",
        tribe=(
            EpistemicTribe
            .TRIBE_A_TECHNOCRATIC.value
        ),
        text=(
            "Obviously the regulator should "
            "automate the process."
        ),
        epistemic_quality=0.30,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-a-003",
        tribe=(
            EpistemicTribe
            .TRIBE_A_TECHNOCRATIC.value
        ),
        text=(
            "Meta-analysis estimates the effect "
            "size at 12 percent (95% CI: 8-16)."
        ),
        epistemic_quality=0.85,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-b-001",
        tribe=(
            EpistemicTribe.TRIBE_B_POPULIST
            .value
        ),
        text=(
            "Real people know the policy is "
            "failing them."
        ),
        epistemic_quality=0.30,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-b-002",
        tribe=(
            EpistemicTribe.TRIBE_B_POPULIST
            .value
        ),
        text=(
            "Survey data shows 62 percent "
            "agree, with margin of error 3."
        ),
        epistemic_quality=0.75,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-b-003",
        tribe=(
            EpistemicTribe.TRIBE_B_POPULIST
            .value
        ),
        text=(
            "Local outcomes contradict the "
            "national narrative."
        ),
        epistemic_quality=0.55,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-c-001",
        tribe=(
            EpistemicTribe.TRIBE_C_TRADITIONAL
            .value
        ),
        text=(
            "Decades of clinical practice "
            "report sustained efficacy."
        ),
        epistemic_quality=0.65,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-c-002",
        tribe=(
            EpistemicTribe.TRIBE_C_TRADITIONAL
            .value
        ),
        text=(
            "If it has always worked, it must "
            "still work."
        ),
        epistemic_quality=0.20,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-c-003",
        tribe=(
            EpistemicTribe.TRIBE_C_TRADITIONAL
            .value
        ),
        text=(
            "A registry of 12000 patients "
            "supports the standard protocol."
        ),
        epistemic_quality=0.80,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-d-001",
        tribe=(
            EpistemicTribe.TRIBE_D_PROGRESSIVE
            .value
        ),
        text=(
            "New experimental evidence revises "
            "the prior estimate downward."
        ),
        epistemic_quality=0.75,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-d-002",
        tribe=(
            EpistemicTribe.TRIBE_D_PROGRESSIVE
            .value
        ),
        text=(
            "The new framework solves all the "
            "old problems."
        ),
        epistemic_quality=0.25,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-d-003",
        tribe=(
            EpistemicTribe.TRIBE_D_PROGRESSIVE
            .value
        ),
        text=(
            "Preregistered replication "
            "confirms the original signal."
        ),
        epistemic_quality=0.85,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-i-001",
        tribe=(
            EpistemicTribe.INDEPENDENT.value
        ),
        text=(
            "A long-running prospective study "
            "estimates a small effect size."
        ),
        epistemic_quality=0.70,
        is_evidence_backed=True,
    ),
    TribalClaim(
        claim_id="t-i-002",
        tribe=(
            EpistemicTribe.INDEPENDENT.value
        ),
        text=(
            "An anecdote from a single clinic."
        ),
        epistemic_quality=0.25,
        is_evidence_backed=False,
    ),
    TribalClaim(
        claim_id="t-i-003",
        tribe=(
            EpistemicTribe.INDEPENDENT.value
        ),
        text=(
            "A peer-reviewed meta-analysis "
            "across 14 cohorts reports moderate "
            "effect size."
        ),
        epistemic_quality=0.90,
        is_evidence_backed=True,
    ),
)


def fixture() -> tuple[TribalClaim, ...]:
    return _FIXTURE


def tribe_counts() -> dict[str, int]:
    from collections import Counter
    return dict(
        Counter(c.tribe for c in fixture())
    )


__all__ = [
    "EPISTEMIC_TRIBES",
    "EpistemicTribe",
    "TribalClaim",
    "fixture",
    "tribe_counts",
]
