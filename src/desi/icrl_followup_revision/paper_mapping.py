"""v23.0 - mapping DESi's central claims to the base
paper's open exploration problems.

The base paper (In-Context RL for Variable Action Spaces and
Skill Stitching) documents open exploration problems,
notably in its Section 4.6: exploration collapse into
repeated suboptimal behaviour, sparse-reward goal
invisibility, repetitive low-information trajectories, and
the difficulty of consistent exploration under variable
action spaces.

Each central DESi claim must anchor to at least one such
problem and cite the sprint it came from. A claim with no
anchor is "generic" and counts against alignment.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplorationProblem:
    problem_id: str
    section: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "problem_id": self.problem_id,
            "section": self.section,
            "text": self.text,
        }


# Open exploration problems the base paper raises (framed
# neutrally; Section 4.6 is the limitations / open-problems
# discussion).
_PROBLEMS: tuple[ExplorationProblem, ...] = (
    ExplorationProblem(
        "P1", "Section 4.6",
        "Exploration can collapse into repeated suboptimal "
        "behaviour."),
    ExplorationProblem(
        "P2", "Section 4.6",
        "Under sparse reward the goal stays undiscovered for "
        "long stretches."),
    ExplorationProblem(
        "P3", "Section 4.6",
        "Repetitive trajectories provide little new "
        "information."),
    ExplorationProblem(
        "P4", "Section 4.6",
        "Variable action spaces complicate consistent "
        "exploration."),
)


@dataclass(frozen=True)
class DesiClaim:
    claim_id: str
    text: str
    sprint_source: str
    anchors: tuple[str, ...]   # base-paper problem ids

    def is_anchored(self) -> bool:
        return bool(self.anchors)

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "sprint_source": self.sprint_source,
            "anchors": list(self.anchors),
            "is_anchored": self.is_anchored(),
        }


# DESi's central claims, each tied to base-paper problems and
# the sprint that produced it.
_CLAIMS: tuple[DesiClaim, ...] = (
    DesiClaim(
        "DC1",
        "A read-only governance layer reduces redundant "
        "search while preserving novel-state reachability.",
        "v19.1", ("P1", "P3")),
    DesiClaim(
        "DC2",
        "Capping high-certainty incoherent paths keeps the "
        "uncontained hallucination rate at zero under "
        "pressure.", "v20.1", ("P1",)),
    DesiClaim(
        "DC3",
        "A generator/governor split raises distinct-state "
        "coverage under sparse-reward-like conditions.",
        "v20.2/v21.0", ("P2", "P1")),
    DesiClaim(
        "DC4",
        "Repetitive loops and dead ends are detected and "
        "deprioritised rather than deleted.", "v19.0/v20.2",
        ("P3", "P1")),
    DesiClaim(
        "DC5",
        "The governance layer keeps exploration plural under "
        "variable-action-space and non-stationary shifts over "
        "a long horizon.", "v19.3/v20.3", ("P4", "P1")),
)


def problems() -> tuple[ExplorationProblem, ...]:
    return _PROBLEMS


def claims() -> tuple[DesiClaim, ...]:
    return _CLAIMS


def by_claim_id(cid: str) -> DesiClaim:
    for c in _CLAIMS:
        if c.claim_id == cid:
            return c
    raise KeyError(cid)


__all__ = [
    "DesiClaim",
    "ExplorationProblem",
    "by_claim_id",
    "claims",
    "problems",
]
