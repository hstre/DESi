"""Canonical PatchCandidates — Aufgaben 4 + 5.

* :func:`causal_chain_v2_7_candidate` — full reconstruction of the
  v2.7 patch, with every guard, observable and touched file
  declared explicitly. Running the protocol on this candidate must
  produce ``phase=PatchPhase.COMPLETE``.

* :func:`fake_rule_without_guards_candidate` — deliberately
  invalid: no guards. Running the protocol on this candidate must
  fail at :class:`PatchPhase.GUARD_SYNTHESIS` with
  ``fail_reason`` starting with ``missing_guards``.
"""
from __future__ import annotations

from .candidate import GuardDescriptor, PatchCandidate


def causal_chain_v2_7_candidate() -> PatchCandidate:
    return PatchCandidate(
        name="causal_chain",
        target_rule="causal_chain",
        source_branch="feature/causal-chain-rule-guarded",
        guards=(
            GuardDescriptor(
                name="contradiction_first_by_iteration_order",
                observable="rule_iteration_order",
                forbidden_shape=(
                    "premise_set_already_matched_by_contradiction"
                ),
            ),
            GuardDescriptor(
                name="premise_kind_atomic_or_particular",
                observable="premise_kind",
                forbidden_shape="universal_conditional_implication_authority",
            ),
            GuardDescriptor(
                name="negation_marker_guard",
                observable="premise_text_substring",
                forbidden_shape="contains_not_or_never_or_none",
            ),
            GuardDescriptor(
                name="quantifier_marker_guard",
                observable="premise_text_substring",
                forbidden_shape="contains_all_every_some_any_each",
            ),
            GuardDescriptor(
                name="cycle_connective_guard",
                observable="premise_text_substring",
                forbidden_shape=(
                    "contains_because_depends_on_requires_relies_on_uses"
                ),
            ),
            GuardDescriptor(
                name="token_in_three_premises_cycle_guard",
                observable="premise_token_graph",
                forbidden_shape="content_token_in_3_or_more_premises",
            ),
            GuardDescriptor(
                name="recycled_conclusion_token_guard",
                observable="conclusion_token_overlap",
                forbidden_shape=(
                    "conclusion_content_token_in_2_or_more_premises"
                ),
            ),
        ),
        touched_files=(
            "src/desi/logic/inference.py",
            "src/desi/rule_audit/categories.py",
            "tests/logic/test_inference.py",
            "tests/logic/test_causal_chain.py",
            "tests/logic/test_causal_chain_regression.py",
            "tests/rule_audit/test_categories.py",
            "docs/memory/v2_7.md",
            "artifacts/v2_7/report.json",
        ),
        required_artifacts=(
            "v2_4/report.json",
            "v2_5/report.json",
            "v2_6/report.json",
        ),
    )


def fake_rule_without_guards_candidate() -> PatchCandidate:
    """An invalid candidate: declares a new rule but offers no
    guards at all. The protocol must reject this at
    GUARD_SYNTHESIS with ``fail_reason`` starting ``missing_guards``.
    """
    return PatchCandidate(
        name="fake_rule",
        target_rule="fake_rule",
        source_branch="feature/v2-8-fail-fixture",
        guards=(),
        touched_files=("src/desi/logic/inference.py",),
        required_artifacts=(
            "v2_4/report.json",
            "v2_5/report.json",
            "v2_6/report.json",
        ),
    )


__all__ = [
    "causal_chain_v2_7_candidate",
    "fake_rule_without_guards_candidate",
]
