"""v12.0 — the "wild brother" hypothesis
explorer.

A closed deterministic generator that produces
a fixed set of Goldbach-flavoured hypotheses
across the six epistemic statuses. The point is
NOT to discover mathematics; the point is to
exercise the audit pipeline with realistic-
looking hypothesis shapes.

The explorer emits a Hypothesis dataclass that
carries the GROUND-TRUTH status (pinned in the
fixture) so the v12.1 governance can be graded
against it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .hypotheses import EpistemicStatus


class HypothesisShape(str, Enum):
    DECOMPOSITION       = "decomposition"
    ASYMPTOTIC          = "asymptotic"
    SYMMETRY            = "symmetry"
    CLUSTER             = "cluster"
    ANALOGY             = "analogy"
    OVERREACH           = "overreach"


HYPOTHESIS_SHAPES: tuple[str, ...] = tuple(
    h.value for h in HypothesisShape
)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    shape: str
    text: str
    ground_truth_status: str
    is_verifiable_locally: bool
    is_overreach: bool
    references_unresolved: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_id":
                self.hypothesis_id,
            "shape": self.shape,
            "text": self.text,
            "ground_truth_status":
                self.ground_truth_status,
            "is_verifiable_locally":
                self.is_verifiable_locally,
            "is_overreach": self.is_overreach,
            "references_unresolved":
                self.references_unresolved,
        }


# A balanced fixture covering all six closed
# statuses. The wild brother emits these; the
# audit must reproduce the pinned status.
_FIXTURE: tuple[Hypothesis, ...] = (
    Hypothesis(
        "hyp-001",
        HypothesisShape.DECOMPOSITION.value,
        "4 = 2 + 2 (both prime, computationally "
        "checked).",
        ground_truth_status=(
            EpistemicStatus.VERIFIED.value
        ),
        is_verifiable_locally=True,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-002",
        HypothesisShape.DECOMPOSITION.value,
        "100 = 3 + 97 (both prime, "
        "computationally checked).",
        ground_truth_status=(
            EpistemicStatus.VERIFIED.value
        ),
        is_verifiable_locally=True,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-003",
        HypothesisShape.DECOMPOSITION.value,
        "1000 = 3 + 997 (both prime, "
        "computationally checked).",
        ground_truth_status=(
            EpistemicStatus.VERIFIED.value
        ),
        is_verifiable_locally=True,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-004",
        HypothesisShape.ASYMPTOTIC.value,
        "The number of Goldbach pairs for "
        "even n grows roughly like n / "
        "(log n)^2 (Hardy-Littlewood "
        "heuristic).",
        ground_truth_status=(
            EpistemicStatus.HEURISTIC.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-005",
        HypothesisShape.ASYMPTOTIC.value,
        "Goldbach pair density seems to "
        "approach a constant for large n.",
        ground_truth_status=(
            EpistemicStatus.HEURISTIC.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-006",
        HypothesisShape.SYMMETRY.value,
        "Goldbach pairs (p, q) for n exhibit "
        "symmetry around n/2 in the empirical "
        "data; this pattern is consistent on "
        "the tested range but is NOT a proof.",
        ground_truth_status=(
            EpistemicStatus.PLAUSIBLE.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-007",
        HypothesisShape.CLUSTER.value,
        "Small even numbers cluster around "
        "decompositions involving 3 or 5; the "
        "pattern weakens for larger n.",
        ground_truth_status=(
            EpistemicStatus.PLAUSIBLE.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-008",
        HypothesisShape.ANALOGY.value,
        "Goldbach decompositions resemble "
        "twin-prime structure; this is an "
        "analogy, not a transfer of proof.",
        ground_truth_status=(
            EpistemicStatus.SPECULATIVE.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=True,
    ),
    Hypothesis(
        "hyp-009",
        HypothesisShape.ANALOGY.value,
        "The Goldbach landscape might be "
        "structurally similar to the "
        "abc-conjecture surface; this is a "
        "loose analogy.",
        ground_truth_status=(
            EpistemicStatus.SPECULATIVE.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=True,
    ),
    Hypothesis(
        "hyp-010",
        HypothesisShape.OVERREACH.value,
        "Every even n > 4 decomposes into two "
        "primes both congruent to 1 mod 6.",
        ground_truth_status=(
            EpistemicStatus.REJECTED.value
        ),
        is_verifiable_locally=True,
        is_overreach=True,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-011",
        HypothesisShape.OVERREACH.value,
        "Goldbach is now solved by the "
        "argument above.",
        ground_truth_status=(
            EpistemicStatus.REJECTED.value
        ),
        is_verifiable_locally=False,
        is_overreach=True,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-012",
        HypothesisShape.OVERREACH.value,
        "Therefore the Goldbach conjecture "
        "follows from the pattern observed "
        "in the first 10 even numbers.",
        ground_truth_status=(
            EpistemicStatus.REJECTED.value
        ),
        is_verifiable_locally=False,
        is_overreach=True,
        references_unresolved=False,
    ),
    Hypothesis(
        "hyp-013",
        HypothesisShape.DECOMPOSITION.value,
        "The Goldbach conjecture itself is "
        "open: every even n > 2 is a sum of "
        "two primes - status remains open.",
        ground_truth_status=(
            EpistemicStatus.UNRESOLVED.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=True,
    ),
    Hypothesis(
        "hyp-014",
        HypothesisShape.SYMMETRY.value,
        "The general structure of Goldbach "
        "pair distributions over all even n "
        "is an open problem.",
        ground_truth_status=(
            EpistemicStatus.UNRESOLVED.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=True,
    ),
    Hypothesis(
        "hyp-015",
        HypothesisShape.CLUSTER.value,
        "Goldbach prime clusters could "
        "perhaps follow an unknown distribution "
        "law - status remains open.",
        ground_truth_status=(
            EpistemicStatus.UNRESOLVED.value
        ),
        is_verifiable_locally=False,
        is_overreach=False,
        references_unresolved=True,
    ),
)


@lru_cache(maxsize=1)
def fixture() -> tuple[Hypothesis, ...]:
    return _FIXTURE


def shape_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        h.shape for h in fixture()
    ))


def status_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        h.ground_truth_status
        for h in fixture()
    ))


__all__ = [
    "HYPOTHESIS_SHAPES",
    "Hypothesis",
    "HypothesisShape",
    "fixture",
    "shape_counts",
    "status_counts",
]
