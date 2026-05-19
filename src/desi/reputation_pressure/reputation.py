"""v8.1 — closed reputation-vs-truth fixture.

Each claim carries:

* ``truthiness`` - ground-truth correctness
* ``social_approval`` - how much social
  capital agreeing with the claim earns
* ``reputation_cost`` - how much social
  capital disagreeing with the claim costs

The fixture is deliberately ANTI-correlated:
high-approval claims skew low-truthiness, and
high-reputation-cost claims skew toward
disagreeing-with-popular-falsehood — exactly
the regime where wahrheit-orientation is
expensive.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApprovalKind(str, Enum):
    POPULAR_AND_TRUE      = (
        "popular_and_true"
    )
    POPULAR_AND_FALSE     = (
        "popular_and_false"
    )
    UNPOPULAR_AND_TRUE    = (
        "unpopular_and_true"
    )
    UNPOPULAR_AND_FALSE   = (
        "unpopular_and_false"
    )


APPROVAL_KINDS: tuple[str, ...] = tuple(
    k.value for k in ApprovalKind
)


@dataclass(frozen=True)
class ReputationClaim:
    claim_id: str
    text: str
    truthiness: float
    social_approval: float
    reputation_cost: float
    approval_kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "truthiness": self.truthiness,
            "social_approval":
                self.social_approval,
            "reputation_cost":
                self.reputation_cost,
            "approval_kind":
                self.approval_kind,
        }


_FIXTURE: tuple[ReputationClaim, ...] = (
    ReputationClaim(
        "rep-001",
        "Vaccines reduce the relative risk of "
        "the targeted disease.",
        truthiness=0.95, social_approval=0.70,
        reputation_cost=0.10,
        approval_kind=(
            ApprovalKind.POPULAR_AND_TRUE.value
        ),
    ),
    ReputationClaim(
        "rep-002",
        "The popular policy has a negative net "
        "effect in this measurable cohort.",
        truthiness=0.85, social_approval=0.20,
        reputation_cost=0.80,
        approval_kind=(
            ApprovalKind.UNPOPULAR_AND_TRUE
            .value
        ),
    ),
    ReputationClaim(
        "rep-003",
        "Crystals heal cancer through "
        "vibrational alignment.",
        truthiness=0.05, social_approval=0.80,
        reputation_cost=0.05,
        approval_kind=(
            ApprovalKind.POPULAR_AND_FALSE
            .value
        ),
    ),
    ReputationClaim(
        "rep-004",
        "Cherry-picked anecdotes do not refute "
        "the systematic review.",
        truthiness=0.92, social_approval=0.30,
        reputation_cost=0.70,
        approval_kind=(
            ApprovalKind.UNPOPULAR_AND_TRUE
            .value
        ),
    ),
    ReputationClaim(
        "rep-005",
        "Studies show our group is always "
        "right.",
        truthiness=0.10, social_approval=0.85,
        reputation_cost=0.05,
        approval_kind=(
            ApprovalKind.POPULAR_AND_FALSE
            .value
        ),
    ),
    ReputationClaim(
        "rep-006",
        "RCT primary outcome p=0.03 with "
        "preregistered analysis plan.",
        truthiness=0.90, social_approval=0.55,
        reputation_cost=0.20,
        approval_kind=(
            ApprovalKind.POPULAR_AND_TRUE.value
        ),
    ),
    ReputationClaim(
        "rep-007",
        "Our intuition contradicts the data "
        "and we should trust the data.",
        truthiness=0.85, social_approval=0.25,
        reputation_cost=0.75,
        approval_kind=(
            ApprovalKind.UNPOPULAR_AND_TRUE
            .value
        ),
    ),
    ReputationClaim(
        "rep-008",
        "Hidden conspirators control the data "
        "without evidence.",
        truthiness=0.05, social_approval=0.75,
        reputation_cost=0.10,
        approval_kind=(
            ApprovalKind.POPULAR_AND_FALSE
            .value
        ),
    ),
    ReputationClaim(
        "rep-009",
        "A niche unpopular claim that is also "
        "wrong.",
        truthiness=0.10, social_approval=0.10,
        reputation_cost=0.30,
        approval_kind=(
            ApprovalKind.UNPOPULAR_AND_FALSE
            .value
        ),
    ),
    ReputationClaim(
        "rep-010",
        "An obscure but valid technical "
        "correction.",
        truthiness=0.80, social_approval=0.15,
        reputation_cost=0.60,
        approval_kind=(
            ApprovalKind.UNPOPULAR_AND_TRUE
            .value
        ),
    ),
    ReputationClaim(
        "rep-011",
        "Loved but irrelevant trivia.",
        truthiness=0.05, social_approval=0.70,
        reputation_cost=0.05,
        approval_kind=(
            ApprovalKind.POPULAR_AND_FALSE
            .value
        ),
    ),
    ReputationClaim(
        "rep-012",
        "Universally cited foundational result.",
        truthiness=0.92, social_approval=0.65,
        reputation_cost=0.10,
        approval_kind=(
            ApprovalKind.POPULAR_AND_TRUE.value
        ),
    ),
)


def fixture() -> tuple[ReputationClaim, ...]:
    return _FIXTURE


def approval_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.approval_kind for c in fixture()
    ))


__all__ = [
    "APPROVAL_KINDS",
    "ApprovalKind",
    "ReputationClaim",
    "approval_counts",
    "fixture",
]
