"""Tests for MutationEvaluation."""
from __future__ import annotations

from desi.evolution import (
    AdversarialPattern,
    CloneSandbox,
    MutationEvaluation,
    MutationProposal,
    MutationTarget,
)
from desi.evolution.evaluation import (
    PFLICHT_SCENARIO_IDS,
    REGRESSION_SCENARIO_IDS,
    adversarial_scenario,
)
from desi.evolution.sandbox import default_stable


def _proposal(stable_version: str) -> MutationProposal:
    return MutationProposal(
        parent_version=stable_version,
        problem="x",
        hypothesis="y",
        target=MutationTarget.GUARD_THRESHOLDS,
        config_delta={"guard_thresholds.merge_similarity_min": 0.90},
        expected_improvement="more conservative merges",
        rollback_conditions=("revert if false-merge rate rises",),
    )


def test_evaluation_runs_all_three_suites() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    clone.apply(_proposal(stable.version))
    report = MutationEvaluation(seed=7).run(clone, "mut_test")
    assert len(report.pflicht_results) == len(PFLICHT_SCENARIO_IDS)
    assert len(report.adversarial_results) == len(list(AdversarialPattern))
    assert len(report.regression_results) == len(REGRESSION_SCENARIO_IDS)


def test_evaluation_pflicht_set_is_S2_S6_S7() -> None:
    assert PFLICHT_SCENARIO_IDS == ("S2", "S6", "S7")


def test_evaluation_adversarial_has_five_patterns() -> None:
    assert {p.value for p in AdversarialPattern} == {
        "branch_explosion", "false_penultimate_candidate",
        "oscillating_novelty", "random_walk", "late_recovery",
    }


def test_adversarial_scenarios_run_without_hook_errors() -> None:
    """Each adversarial pattern must complete with no hook errors."""
    from desi.eval import EvaluationHarness
    harness = EvaluationHarness(model="m")
    for pat in AdversarialPattern:
        result = harness.run_scenario(adversarial_scenario(pat), seed=0)
        assert not result.hook_errors, (
            f"adversarial pattern {pat.value} produced hook errors: "
            f"{result.hook_errors}"
        )


def test_all_green_property_aggregates_three_suites() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    clone.apply(_proposal(stable.version))
    report = MutationEvaluation().run(clone, "mut_g")
    assert report.all_green == (
        report.passed_pflicht
        and report.passed_adversarial
        and report.passed_regression
    )


def test_regressions_detected_is_empty_on_clean_run() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    clone.apply(_proposal(stable.version))
    report = MutationEvaluation().run(clone, "mut_clean")
    if report.all_green:
        assert report.regressions_detected == []
