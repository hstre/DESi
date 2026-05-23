"""v31.3 - branch ecology of the peripheral mutation generations.

Read-only view of the branch population produced by the 25
generations: every branch is isolated under the proposal branch,
none targets main, and the protected core stays byte-invariant
across the whole ecology (zero core drift).
"""
from __future__ import annotations

from desi.peripheral_mutation_real import BRANCH

from .mutation_generations import core_preservation, run
from .mutation_lineage import branch_ids, root_branch, targets_main

PROPOSAL_BRANCH = BRANCH
MAIN_BRANCH = "main"


def branches() -> tuple[str, ...]:
    return branch_ids()


def branch_count() -> int:
    return len(branch_ids())


def all_branch_isolated() -> bool:
    """Every generation branch lives under the proposal branch and
    none of them is main."""
    prefix = PROPOSAL_BRANCH + "/"
    for b in branch_ids():
        if b == MAIN_BRANCH or not b.startswith(prefix):
            return False
    return root_branch() == PROPOSAL_BRANCH


def core_drift() -> bool:
    """True if the protected-core fingerprint drifted in any
    generation."""
    return core_preservation() < 1.0


def core_drift_count() -> int:
    return sum(1 for r in run().records if not r.core_preserved)


def targets_main_branch() -> bool:
    return targets_main()


__all__ = [
    "MAIN_BRANCH",
    "PROPOSAL_BRANCH",
    "all_branch_isolated",
    "branch_count",
    "branches",
    "core_drift",
    "core_drift_count",
    "targets_main_branch",
]
