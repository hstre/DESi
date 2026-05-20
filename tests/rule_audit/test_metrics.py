"""Tests for v2.5 rule-coverage metrics (Aufgabe 6)."""
from __future__ import annotations

from desi.rule_audit import (
    AttemptedRule,
    MissingRuleClass,
    RuleCoverageRunner,
    compute_rule_coverage_metrics,
    dominant_missing_rule_class,
)


def test_metrics_carry_required_observables() -> None:
    run = RuleCoverageRunner().run()
    m = compute_rule_coverage_metrics(run)
    for f in (
        "rule_hit_rate", "no_rule_match_rate",
        "parser_vs_rule_misclassification_rate",
        "per_rule_hit_counts", "missing_rule_distribution",
        "per_category_rule_coverage", "multi_hop_case_coverage",
    ):
        assert hasattr(m, f), f


def test_rates_are_in_unit_interval() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    for r in (
        m.rule_hit_rate, m.no_rule_match_rate,
        m.parser_vs_rule_misclassification_rate,
        m.multi_hop_case_coverage,
    ):
        assert 0.0 <= r <= 1.0


def test_per_rule_hit_counts_use_closed_enum_keys() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    enum_values = {r.value for r in AttemptedRule}
    for k in m.per_rule_hit_counts:
        assert k in enum_values


def test_missing_rule_distribution_uses_closed_enum_keys() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    enum_values = {x.value for x in MissingRuleClass}
    assert set(m.missing_rule_distribution.keys()) == enum_values


def test_missing_rule_distribution_sums_to_total() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    assert sum(m.missing_rule_distribution.values()) == m.total


def test_per_category_covers_five_categories() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    assert len(m.per_category_rule_coverage) == 5


def test_per_category_each_sums_to_six() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    for cat, dist in m.per_category_rule_coverage.items():
        assert sum(dist.values()) == 6, cat


def test_metrics_are_deterministic_across_two_runs() -> None:
    a = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    b = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    assert a.to_dict() == b.to_dict()


def test_dominant_missing_rule_returns_enum_member() -> None:
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    d = dominant_missing_rule_class(m)
    assert d in set(MissingRuleClass)


def test_misclassification_rate_lower_bound_on_real_run() -> None:
    """The directive's empirical question — the rate must report a
    real number, and on the v2.3 cases (where premises are
    extracted but no rule matches) it must be > 0."""
    m = compute_rule_coverage_metrics(RuleCoverageRunner().run())
    assert m.parser_vs_rule_misclassification_rate > 0.0
