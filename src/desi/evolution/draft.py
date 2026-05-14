"""ProposalDraftBuilder — non-ratified Proposal drafts from ReflectionFinding.

v0.6 introduces a helper that translates one :class:`ReflectionFinding`
into a draft :class:`MutationProposal`. The draft is **not** promotable:
it carries ``requires_ratification=True`` so that downstream governance
refuses to promote it until a human ratifier sets the flag to False.

The mapping from a finding to a config_delta is deliberately
conservative. The draft proposes the smallest reasonable knob nudge
based on `affected_components`. The point is to seed the conversation,
not to replace human judgement.
"""
from __future__ import annotations

from typing import Any

from .proposal import MutationProposal, MutationTarget
from .reflection import ReflectionFinding


# Mapping from finding.affected_components hints to a (target, knob, value).
# Default nudges are small and reversible. If no mapping fits, we still
# produce a draft, but with empty config_delta so the Skeptiker vetos it
# unless the ratifier fills it in.
_COMPONENT_NUDGES: dict[str, tuple[MutationTarget, str, Any]] = {
    "branch_heuristics": (
        MutationTarget.BRANCH_HEURISTICS,
        "guard_thresholds.branch_open_evidence_min",
        0.45,
    ),
    "merge_policy": (
        MutationTarget.MERGE_POLICY,
        "guard_thresholds.merge_similarity_min",
        0.90,
    ),
    "guard_thresholds": (
        MutationTarget.GUARD_THRESHOLDS,
        "guard_thresholds.merge_similarity_min",
        0.90,
    ),
    "operator_ordering": (
        MutationTarget.OPERATOR_ORDERING,
        "operator_ordering.commit_after_n_consistent_steps",
        4,
    ),
    "diagnostics": (
        MutationTarget.DIAGNOSTICS,
        "diagnostics.late_guard_percentile",
        0.80,
    ),
}


class ProposalDraftBuilder:
    """Builds a non-ratified Proposal draft from a ReflectionFinding.

    The builder is intentionally minimal. It does not consult the
    full ledger or the memory layer; that's a v0.7 question. v0.6
    only commits to providing the *shape* of a draft so that a human
    or a future LLM-supported ratifier can fill in the details.
    """

    def __init__(self, *, default_stable_version: str) -> None:
        self.default_stable_version = default_stable_version

    def draft(
        self,
        finding: ReflectionFinding,
        *,
        stable_version: str | None = None,
        motivating_finding_id: str = "",
    ) -> MutationProposal:
        target, knob, value = self._pick_nudge(finding)
        return MutationProposal(
            parent_version=stable_version or self.default_stable_version,
            problem=finding.observed_problem,
            hypothesis=(
                f"Adjust {knob} (suspected root cause: "
                f"{finding.suspected_root_cause})"
                if knob else
                "Manual ratification required — automatic mapping "
                "could not identify a single-knob nudge."
            ),
            target=target,
            config_delta={knob: value} if knob else {},
            expected_improvement=(
                f"Expect the finding's supporting events "
                f"({len(finding.supporting_events)} ticks) to drop on "
                f"the next evaluation pass."
            ),
            rollback_conditions=(
                f"revert if the metric that triggered this finding "
                f"(category={finding.category!r}) gets worse on the "
                "Pflichtsuite",
            ),
            motivating_findings=(
                (motivating_finding_id,) if motivating_finding_id else ()
            ),
            requires_ratification=True,
        )

    @staticmethod
    def _pick_nudge(
        finding: ReflectionFinding,
    ) -> tuple[MutationTarget, str, Any]:
        for component in finding.affected_components:
            if component in _COMPONENT_NUDGES:
                return _COMPONENT_NUDGES[component]
        # Fallback: target guard_thresholds with no actual knob change.
        return (MutationTarget.GUARD_THRESHOLDS, "", None)


__all__ = ["ProposalDraftBuilder"]
