"""Catalogue of named mutations (v0.7+).

A named mutation is a fixed :class:`MutationProposal` value that the
research team can refer to by ID across multiple runs. M-001 is the
first behaviour-effective mutation in DESi's evolution.
"""
from __future__ import annotations

from .proposal import MutationProposal, MutationTarget
from .sandbox import default_stable


# ---------------------------------------------------------------------------
# M-001 — branch_open_evidence_min: 0.30 → 0.45
# ---------------------------------------------------------------------------


def m_001() -> MutationProposal:
    """First real, behaviour-effective mutation.

    Raises the branch-open-evidence threshold from the stable default
    of 0.30 to 0.45. Under v0.7's deterministic evidence function
    (see :class:`desi.observe.session._SessionHook`), this suppresses
    branch opens once enough branches have already been opened in
    quick succession — exactly the failure mode that
    ``ADV_BRANCH_EXPLOSION`` targets.

    Hypothesis (load-bearing):

      Fewer unnecessary branches on branch_explosion-style trajectories,
      with NO loss of contradiction detection on S2 and NO loss of
      merge-rejection on S6.

    Rollback conditions:

      R1 — S2 loses any CONTRADICTS edge
      R2 — S6 loses its guard_blocked event
      R3 — branch_opened on ADV_BRANCH_EXPLOSION does not strictly decrease
      R4 — any hook error appears under the new threshold
    """
    return MutationProposal(
        mutation_id="M-001",
        parent_version=default_stable().version,
        problem=(
            "On ADV_BRANCH_EXPLOSION the v0.6 stable opens a new branch "
            "on every distinct focus_claim_id without considering "
            "evidence accumulation. Six branches open in six steps; "
            "the path-quality counter (branch_opened_count = 6) is "
            "the largest of the v0.6 baseline."
        ),
        hypothesis=(
            "Raising guard_thresholds.branch_open_evidence_min from "
            "0.30 to 0.45 should suppress branch opens after the third "
            "consecutive newly-introduced focus, reducing "
            "branch_opened_count on ADV_BRANCH_EXPLOSION by at least "
            "two while leaving S2 (contradiction detection) and S6 "
            "(refused-merge guard) byte-identical."
        ),
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={
            "guard_thresholds.branch_open_evidence_min": 0.45,
        },
        expected_improvement=(
            "branch_opened_count on ADV_BRANCH_EXPLOSION drops by >= 2 "
            "compared to the stable run with the default threshold "
            "(0.30); MetricsDelta.verdict for that scenario reads "
            "'improved'."
        ),
        rollback_conditions=(
            "R1: revert if S2 contradicts_count falls below the stable "
            "value (CONTRADICTS detection lost)",
            "R2: revert if S6 guard_blocked_count falls below the "
            "stable value (merge-rejection lost)",
            "R3: revert if ADV_BRANCH_EXPLOSION branch_opened_count "
            "is not strictly less than stable",
            "R4: revert if any hook_error_count delta is > 0 in any "
            "evaluated scenario",
        ),
        motivating_findings=("rf_branch_overopen",),
    )


# Public mutation catalogue keyed by id. v0.7 ships exactly one entry.
NAMED_MUTATIONS: dict[str, callable] = {
    "M-001": m_001,
}


def mutation_by_id(mutation_id: str) -> MutationProposal:
    """Return a fresh proposal instance for the named mutation."""
    if mutation_id not in NAMED_MUTATIONS:
        raise KeyError(
            f"unknown named mutation: {mutation_id!r}; "
            f"v0.7 catalogue contains {sorted(NAMED_MUTATIONS)}"
        )
    return NAMED_MUTATIONS[mutation_id]()


__all__ = [
    "NAMED_MUTATIONS",
    "m_001",
    "mutation_by_id",
]
