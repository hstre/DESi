"""v11.1 — DESi search-governance policy.

DESi applies a CLOSED prioritisation rule over
v11.0's classified branches:

* FORCED        -> ALWAYS keep (it carries the
                   highest information density)
* KEEP          -> ALWAYS keep (substantive)
* LOW_INFO      -> deprioritise (skipped from
                   active search, replay-cached)
* REDUNDANT     -> deprioritise

Plus an OVERRIDE: every branch whose ground-
truth ``is_critical_tactic`` flag is True is
ALWAYS kept regardless of its verdict. The
critical-tactic override is the structural
guarantee against losing forced mates / sac
combinations.

DESi MUST NOT:
* mutate the engine evaluation
* filter illegal moves
* inject hidden heuristics

This module only re-orders / suppresses search
visits over the v11.0 closed enums.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..chess_governance.redundancy import (
    BranchVerdict, classified_branches,
)


class GovernanceAction(str, Enum):
    SEARCH    = "search"
    SKIP      = "skip"
    REPLAY    = "replay"


GOVERNANCE_ACTIONS: tuple[str, ...] = tuple(
    a.value for a in GovernanceAction
)


@dataclass(frozen=True)
class GovernedBranch:
    branch_id: str
    position_id: str
    verdict: str
    action: str
    is_critical_truth: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "position_id": self.position_id,
            "verdict": self.verdict,
            "action": self.action,
            "is_critical_truth":
                self.is_critical_truth,
        }


def _action_for(
    verdict: str, is_critical: bool,
) -> GovernanceAction:
    # Critical-tactic override always wins.
    if is_critical:
        return GovernanceAction.SEARCH
    if verdict == BranchVerdict.FORCED.value:
        return GovernanceAction.SEARCH
    if verdict == BranchVerdict.KEEP.value:
        return GovernanceAction.SEARCH
    if verdict == BranchVerdict.REDUNDANT.value:
        return GovernanceAction.REPLAY
    if verdict == BranchVerdict.LOW_INFO.value:
        return GovernanceAction.SKIP
    # Closed enum exhausted - default skip.
    return GovernanceAction.SKIP


@lru_cache(maxsize=1)
def governed_branches() -> tuple[
    GovernedBranch, ...,
]:
    return tuple(
        GovernedBranch(
            branch_id=c.branch_id,
            position_id=c.position_id,
            verdict=c.verdict,
            action=_action_for(
                c.verdict,
                c.is_critical_truth,
            ).value,
            is_critical_truth=(
                c.is_critical_truth
            ),
        )
        for c in classified_branches()
    )


def action_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        g.action for g in governed_branches()
    ))


__all__ = [
    "GOVERNANCE_ACTIONS",
    "GovernanceAction",
    "GovernedBranch",
    "action_counts",
    "governed_branches",
]
