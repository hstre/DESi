"""Tests for v0.9 multi-seed evaluation under real scenario variance.

When the SeededScenarioEngine is plugged in, the multi-seed runner
must (a) produce std > 0 on the candidate scenario's per-seed
branch-delta, (b) still pass the SignificanceGate for M-001 (because
4/5 of the mandatory seeds remain improved), and (c) populate the
new ``permutation_coverage`` and ``unique_path_count`` fields.
"""
from __future__ import annotations

from desi.eval import SeededScenarioEngine
from desi.evolution import (
    CloneSandbox,
    DEFAULT_SEEDS,
    MultiSeedMutationEvaluation,
    SignificanceGate,
    m_001,
)
from desi.evolution.sandbox import default_stable


def _eval(*, include_stress: bool = False):
    engine = SeededScenarioEngine()
    clone = CloneSandbox(default_stable())
    p = m_001()
    clone.apply(p)
    return MultiSeedMutationEvaluation(
        engine=engine, include_stress=include_stress,
    ).run(clone, p.mutation_id)


# ---------------------------------------------------------------------------
# Variance is real
# ---------------------------------------------------------------------------


def test_seed_variant_runs_produce_std_gt_zero_on_branch_delta() -> None:
    report = _eval()
    adv = report.aggregates["ADV_BRANCH_EXPLOSION"]
    assert adv.std_branch_delta > 0.0, (
        f"std_branch_delta={adv.std_branch_delta}; "
        f"variance should be > 0 on a seed-variant scenario."
    )


def test_per_seed_verdicts_are_not_all_identical_on_variant() -> None:
    report = _eval()
    adv = report.aggregates["ADV_BRANCH_EXPLOSION"]
    assert len(set(adv.per_seed_verdicts)) >= 2, (
        f"per-seed verdicts on a seed-variant scenario should differ; "
        f"got {adv.per_seed_verdicts}"
    )


# ---------------------------------------------------------------------------
# permutation_coverage + unique_path_count
# ---------------------------------------------------------------------------


def test_permutation_coverage_is_five_for_seeded_variant_scenarios() -> None:
    report = _eval()
    assert report.permutation_coverage["ADV_BRANCH_EXPLOSION"] == 5
    assert report.permutation_coverage["S2"] == 5
    assert report.permutation_coverage["S6"] == 5


def test_permutation_coverage_is_one_for_static_scenarios() -> None:
    report = _eval()
    # S5 has no variant generator → coverage is 1.
    assert report.permutation_coverage["S5"] == 1


def test_unique_path_count_matches_distinct_branch_signatures() -> None:
    report = _eval()
    paths = report.unique_path_count
    # ADV_BRANCH_EXPLOSION should walk a different path on every seed.
    assert paths["ADV_BRANCH_EXPLOSION"] >= 4


# ---------------------------------------------------------------------------
# generation_metadata is captured per (scenario, seed)
# ---------------------------------------------------------------------------


def test_generation_metadata_keyed_by_scenario_and_seed() -> None:
    report = _eval()
    assert ("ADV_BRANCH_EXPLOSION", 42) in report.generation_metadata
    meta = report.generation_metadata[("ADV_BRANCH_EXPLOSION", 42)]
    assert meta.seed == 42
    assert meta.permutation_id != "static"


def test_static_scenario_metadata_is_marked_static() -> None:
    report = _eval()
    meta = report.generation_metadata[("S5", 42)]
    assert meta.permutation_id == "static"


# ---------------------------------------------------------------------------
# M-001 STILL holds under variance — the v0.9 acid test.
# ---------------------------------------------------------------------------


def test_m001_significance_gate_still_improved_under_variance() -> None:
    report = _eval()
    decision = SignificanceGate().decide(report)
    assert decision.verdict == "improved", (
        f"M-001 must still pass the gate under seed-variant scenarios; "
        f"got verdict={decision.verdict}, rationale={decision.rationale}"
    )
    # At least 4 of the 5 mandatory seeds must support.
    assert len(decision.supporting_seeds) >= 4
    # Zero failing seeds (a failing seed is a regression, not a neutral).
    assert decision.failing_seeds == ()


def test_m001_holds_with_stress_seed_included() -> None:
    report = _eval(include_stress=True)
    assert report.stress_outcome is not None
    # Stress seed under the seed-variant should still not produce a
    # regression on this scenario design.
    assert report.stress_outcome.delta.verdict != "regressed"


# ---------------------------------------------------------------------------
# Backwards compatibility: no engine → v0.8 behaviour preserved.
# ---------------------------------------------------------------------------


def test_runner_without_engine_matches_v08_behaviour() -> None:
    """When engine is not supplied, std==0 on the static scenario
    set (the v0.8 regime). Variance is opt-in."""
    clone = CloneSandbox(default_stable())
    p = m_001()
    clone.apply(p)
    report = MultiSeedMutationEvaluation().run(clone, p.mutation_id)
    for agg in report.aggregates.values():
        assert agg.std_branch_delta == 0.0
