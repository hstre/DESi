"""Tests for M-001 — first real mutation."""
from __future__ import annotations

from desi.evolution import (
    AdversarialPattern,
    CloneSandbox,
    MutationProposal,
    MutationTarget,
    NAMED_MUTATIONS,
    PairedMutationEvaluation,
    m_001,
    mutation_by_id,
)
from desi.evolution.sandbox import default_stable


# ---------------------------------------------------------------------------
# Mutation catalogue
# ---------------------------------------------------------------------------


def test_named_mutations_catalogue_contains_M001() -> None:
    assert "M-001" in NAMED_MUTATIONS


def test_mutation_by_id_returns_M001() -> None:
    p = mutation_by_id("M-001")
    assert p.mutation_id == "M-001"
    assert p.target is MutationTarget.BRANCH_HEURISTICS
    assert "guard_thresholds.branch_open_evidence_min" in p.config_delta
    assert p.config_delta["guard_thresholds.branch_open_evidence_min"] == 0.45


def test_mutation_by_id_rejects_unknown_id() -> None:
    import pytest
    with pytest.raises(KeyError):
        mutation_by_id("M-999")


def test_M001_has_four_rollback_conditions() -> None:
    p = m_001()
    assert len(p.rollback_conditions) >= 4
    # The four rollback conditions reference S2, S6, branch_explosion,
    # and hook errors respectively.
    joined = " ".join(p.rollback_conditions)
    assert "S2" in joined
    assert "S6" in joined
    assert "BRANCH_EXPLOSION" in joined.upper()
    assert "hook" in joined.lower()


# ---------------------------------------------------------------------------
# Paired evaluation: M-001 must improve on explosion without regressing
# S2 / S6
# ---------------------------------------------------------------------------


def _eval_m001() -> "PairedEvaluationReport":  # noqa: F821
    stable = default_stable()
    clone = CloneSandbox(stable)
    p = m_001()
    clone.apply(p)
    return PairedMutationEvaluation(seed=42).run(clone, p.mutation_id)


def test_M001_reduces_branches_on_branch_explosion() -> None:
    report = _eval_m001()
    explosion = next(
        o for o in report.outcomes
        if o.scenario_id == f"ADV_{AdversarialPattern.BRANCH_EXPLOSION.name}"
    )
    assert explosion.delta.branch_opened_delta < 0
    assert explosion.delta.verdict == "improved"


def test_M001_preserves_S2_contradiction_detection() -> None:
    report = _eval_m001()
    s2 = next(o for o in report.outcomes if o.scenario_id == "S2")
    assert s2.delta.contradicts_delta == 0
    assert s2.delta.verdict != "regressed"


def test_M001_preserves_S6_merge_refusal() -> None:
    report = _eval_m001()
    s6 = next(o for o in report.outcomes if o.scenario_id == "S6")
    assert s6.delta.merged_into_delta == 0
    assert s6.delta.guard_blocked_delta == 0  # the post_run guard fires under both
    assert s6.delta.verdict != "regressed"


def test_M001_aggregate_verdict_is_improved() -> None:
    report = _eval_m001()
    assert report.aggregate_verdict == "improved"
    assert report.passed_evolution_candidate
    assert report.passed_regression_guards


def test_M001_no_hook_errors_under_either_config() -> None:
    report = _eval_m001()
    for o in report.outcomes:
        assert o.stable_metrics.hook_error_count == 0
        assert o.clone_metrics.hook_error_count == 0
