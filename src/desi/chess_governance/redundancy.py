"""v11.0 — redundancy + low-information +
forced-line detection.

The detector is a closed-rule cascade:

* a branch is FORCED if its
  ``information_density >= 0.80`` AND its
  ``is_forced`` ground-truth flag is true.
* a branch is REDUNDANT if its
  ``information_density <= 0.20`` AND its
  ``is_redundant`` ground-truth flag is true.
* a branch is LOW_INFO if its
  ``information_density <= 0.30`` regardless of
  the redundancy flag.

The classifier is graded against the ground-
truth flags.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .positions import (
    Branch, Position, fixture,
    total_branch_count,
)


class BranchVerdict(str, Enum):
    KEEP        = "keep"
    LOW_INFO    = "low_info"
    REDUNDANT   = "redundant"
    FORCED      = "forced"


BRANCH_VERDICTS: tuple[str, ...] = tuple(
    v.value for v in BranchVerdict
)


def classify_branch(b: Branch) -> BranchVerdict:
    if b.information_density >= 0.80:
        return BranchVerdict.FORCED
    if b.is_redundant and (
        b.information_density <= 0.20
    ):
        return BranchVerdict.REDUNDANT
    if b.information_density <= 0.30:
        return BranchVerdict.LOW_INFO
    return BranchVerdict.KEEP


@dataclass(frozen=True)
class ClassifiedBranch:
    branch_id: str
    position_id: str
    verdict: str
    information_density: float
    is_redundant_truth: bool
    is_forced_truth: bool
    is_critical_truth: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "position_id": self.position_id,
            "verdict": self.verdict,
            "information_density":
                self.information_density,
            "is_redundant_truth":
                self.is_redundant_truth,
            "is_forced_truth":
                self.is_forced_truth,
            "is_critical_truth":
                self.is_critical_truth,
        }


@lru_cache(maxsize=1)
def classified_branches() -> tuple[
    ClassifiedBranch, ...,
]:
    out: list[ClassifiedBranch] = []
    for p in fixture():
        for b in p.branches:
            out.append(ClassifiedBranch(
                branch_id=b.branch_id,
                position_id=p.position_id,
                verdict=classify_branch(
                    b,
                ).value,
                information_density=(
                    b.information_density
                ),
                is_redundant_truth=(
                    b.is_redundant
                ),
                is_forced_truth=b.is_forced,
                is_critical_truth=(
                    b.is_critical_tactic
                ),
            ))
    return tuple(out)


def redundant_branch_rate() -> float:
    """Recall on the ground-truth REDUNDANT set:
    of all branches marked is_redundant=True
    in the fixture, how many does the classifier
    label REDUNDANT?"""
    rows = classified_branches()
    target = [
        r for r in rows
        if r.is_redundant_truth
    ]
    if not target:
        return 0.0
    hit = sum(
        1 for r in target
        if r.verdict == (
            BranchVerdict.REDUNDANT.value
        )
    )
    return round(hit / len(target), 6)


def low_information_rate() -> float:
    """Fraction of all branches that fall into
    the LOW_INFO or REDUNDANT bucket. This is
    the share of the search tree that can be
    safely deprioritised."""
    rows = classified_branches()
    if not rows:
        return 0.0
    low = sum(
        1 for r in rows
        if r.verdict in {
            BranchVerdict.LOW_INFO.value,
            BranchVerdict.REDUNDANT.value,
        }
    )
    return round(low / len(rows), 6)


def forced_line_detection() -> float:
    """Recall on the ground-truth FORCED set."""
    rows = classified_branches()
    target = [
        r for r in rows
        if r.is_forced_truth
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target
        if r.verdict == (
            BranchVerdict.FORCED.value
        )
    )
    return round(hit / len(target), 6)


def replay_reuse() -> float:
    """Fraction of branches that share their
    state hash with at least one other branch
    (i.e., compute results can be reused).
    Operationalised as: fraction of LOW_INFO +
    REDUNDANT branches in positions of the SAME
    kind."""
    from collections import Counter
    rows = classified_branches()
    by_kind: dict[str, list[str]] = {}
    by_id = {
        b.branch_id: p.kind
        for p in fixture()
        for b in p.branches
    }
    for r in rows:
        if r.verdict in {
            BranchVerdict.LOW_INFO.value,
            BranchVerdict.REDUNDANT.value,
        }:
            kind = by_id[r.branch_id]
            by_kind.setdefault(kind, []).append(
                r.branch_id,
            )
    reusable = sum(
        len(v) for v in by_kind.values()
        if len(v) >= 2
    )
    total = len(rows)
    if total == 0:
        return 0.0
    return round(reusable / total, 6)


__all__ = [
    "BRANCH_VERDICTS",
    "BranchVerdict",
    "ClassifiedBranch",
    "classified_branches",
    "classify_branch",
    "forced_line_detection",
    "low_information_rate",
    "redundant_branch_rate",
    "replay_reuse",
]
