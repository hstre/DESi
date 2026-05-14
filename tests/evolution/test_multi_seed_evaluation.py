"""Tests for v0.8 MultiSeedMutationEvaluation — N-seed paired runs."""
from __future__ import annotations

from desi.evolution import (
    CloneSandbox,
    DEFAULT_SEEDS,
    MultiSeedEvaluationReport,
    MultiSeedMutationEvaluation,
    PairedEvaluationReport,
    m_001,
)
from desi.evolution.sandbox import default_stable


def _eval(*, include_stress: bool = False) -> MultiSeedEvaluationReport:
    stable = default_stable()
    clone = CloneSandbox(stable)
    p = m_001()
    clone.apply(p)
    return MultiSeedMutationEvaluation(
        include_stress=include_stress,
    ).run(clone, p.mutation_id)


# ---------------------------------------------------------------------------
# Seed list contract: exactly 5 seeds, deterministic, mandatory values
# ---------------------------------------------------------------------------


def test_default_seeds_are_exactly_five() -> None:
    assert len(DEFAULT_SEEDS) == 5


def test_default_seeds_are_the_v08_mandatory_list() -> None:
    assert DEFAULT_SEEDS == (42, 43, 44, 45, 46)


def test_runner_uses_default_seeds_when_none_supplied() -> None:
    runner = MultiSeedMutationEvaluation()
    assert runner.seeds == DEFAULT_SEEDS


def test_runner_rejects_duplicate_seeds() -> None:
    import pytest
    with pytest.raises(ValueError):
        MultiSeedMutationEvaluation(seeds=(42, 42, 43, 44, 45))


def test_runner_rejects_empty_seed_list() -> None:
    import pytest
    with pytest.raises(ValueError):
        MultiSeedMutationEvaluation(seeds=())


# ---------------------------------------------------------------------------
# Output shape: report contains the right metadata + N per-seed reports
# ---------------------------------------------------------------------------


def test_report_carries_exactly_five_per_seed_reports() -> None:
    report = _eval()
    assert len(report.per_seed_reports) == 5
    assert all(isinstance(r, PairedEvaluationReport)
               for r in report.per_seed_reports)


def test_report_metadata_is_populated() -> None:
    report = _eval()
    assert report.mutation_id == "M-001"
    assert report.parent_version  # stable-v0.5.0 or similar
    assert report.clone_id
    assert report.seeds == DEFAULT_SEEDS
    # The closed v0.7 scenario set: S5, ADV_BRANCH_EXPLOSION, S2, S6
    assert "S5" in report.scenario_ids
    assert "ADV_BRANCH_EXPLOSION" in report.scenario_ids
    assert "S2" in report.scenario_ids
    assert "S6" in report.scenario_ids


def test_report_aggregates_cover_every_scenario() -> None:
    report = _eval()
    for sid in report.scenario_ids:
        assert sid in report.aggregates
        assert report.aggregates[sid].n_seeds == 5


# ---------------------------------------------------------------------------
# Determinism: same clone + same seeds → same aggregate metrics
# ---------------------------------------------------------------------------


def test_multi_seed_evaluation_is_deterministic() -> None:
    a = _eval()
    b = _eval()
    for sid in a.scenario_ids:
        agg_a = a.aggregates[sid]
        agg_b = b.aggregates[sid]
        assert agg_a.mean_branch_delta == agg_b.mean_branch_delta
        assert agg_a.median_branch_delta == agg_b.median_branch_delta
        assert agg_a.std_branch_delta == agg_b.std_branch_delta
        assert agg_a.per_seed_verdicts == agg_b.per_seed_verdicts


# ---------------------------------------------------------------------------
# Stress seed: optional, logs ADV_BRANCH_EXPLOSION only, not gate-relevant
# ---------------------------------------------------------------------------


def test_stress_seed_is_off_by_default() -> None:
    report = _eval(include_stress=False)
    assert report.stress_outcome is None


def test_stress_seed_can_be_enabled_and_runs_only_explosion() -> None:
    report = _eval(include_stress=True)
    assert report.stress_outcome is not None
    assert report.stress_outcome.scenario_id == "ADV_BRANCH_EXPLOSION"
