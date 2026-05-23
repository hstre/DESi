"""v23.3 - model of what a base-paper author cares about.

Enumerates the dimensions a base-paper author would weigh
when judging whether a follow-up directly continues their
open exploration question (Section 4.6). Each interest is
marked addressed or not by querying the lower follow-up
layers (v23.0 anchoring, v23.1 reconstruction, v23.2 density),
so relevance is measured against real signals, not asserted.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_followup_revision import addressed_problem_ids
from desi.icrl_followup_conditions import result_traceability
from desi.icrl_followup_density import (
    claim_conservatism, scientific_density,
)


@dataclass(frozen=True)
class AuthorInterest:
    interest_id: str
    topic: str
    addressed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "interest_id": self.interest_id,
            "topic": self.topic,
            "addressed": self.addressed,
        }


def _interests() -> tuple[AuthorInterest, ...]:
    addressed = set(addressed_problem_ids())
    return (
        AuthorInterest(
            "I1",
            "Mitigating exploration collapse (Section 4.6)",
            "P1" in addressed),
        AuthorInterest(
            "I2",
            "Sparse-reward exploration failure",
            "P2" in addressed),
        AuthorInterest(
            "I3",
            "Repetitive-trajectory failure",
            "P3" in addressed),
        AuthorInterest(
            "I4",
            "Variable action spaces and skill stitching",
            "P4" in addressed),
        AuthorInterest(
            "I5",
            "Reproducible, auditable results",
            result_traceability() >= 0.90),
        AuthorInterest(
            "I6",
            "Honest scope without overclaiming",
            claim_conservatism() >= 0.90),
        AuthorInterest(
            "I7",
            "Concrete mechanisms over vague framing",
            scientific_density() >= 0.90),
    )


def author_interests() -> tuple[AuthorInterest, ...]:
    return _interests()


def interest_topics() -> tuple[str, ...]:
    return tuple(i.topic for i in _interests())


__all__ = [
    "AuthorInterest",
    "author_interests",
    "interest_topics",
]
