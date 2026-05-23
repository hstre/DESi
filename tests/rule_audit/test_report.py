"""Tests for v2.5 RuleCoverageReport (Aufgabe 6 + replay)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.rule_audit import (
    MissingRuleClass,
    RuleCoverageReport,
    RuleCoverageRunner,
    build_rule_coverage_report,
    compute_report_replay_hash,
)


def _report() -> RuleCoverageReport:
    now = datetime.now(timezone.utc)
    return build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )


def test_report_carries_all_required_fields() -> None:
    rep = _report()
    for f in (
        "total_cases", "rule_hit_rate", "no_rule_match_rate",
        "parser_vs_rule_misclassification_rate",
        "per_rule_hit_counts", "missing_rule_distribution",
        "per_category_rule_coverage", "multi_hop_case_coverage",
        "dominant_missing_rule_class", "replay_hash",
    ):
        assert hasattr(rep, f), f


def test_total_cases_is_thirty() -> None:
    rep = _report()
    assert rep.total_cases == 30


def test_dominant_missing_rule_is_enum_member() -> None:
    rep = _report()
    assert rep.dominant_missing_rule_class in set(MissingRuleClass)


def test_two_runs_produce_identical_replay_hash() -> None:
    now = datetime.now(timezone.utc)
    a = build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )
    b = build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    early = datetime(2020, 1, 1, tzinfo=timezone.utc)
    late = datetime(2030, 1, 1, tzinfo=timezone.utc)
    run = RuleCoverageRunner().run()
    a = build_rule_coverage_report(run, started_at=early, finished_at=early)
    b = build_rule_coverage_report(run, started_at=late, finished_at=late)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_helper_is_sixteen_hex_chars() -> None:
    h = compute_report_replay_hash({"total_cases": 30})
    assert len(h) == 16
    int(h, 16)


def test_to_dict_round_trip_shape() -> None:
    rep = _report()
    d = rep.to_dict()
    for k in (
        "total_cases", "rule_hit_rate", "no_rule_match_rate",
        "parser_vs_rule_misclassification_rate",
        "per_rule_hit_counts", "missing_rule_distribution",
        "per_category_rule_coverage", "multi_hop_case_coverage",
        "dominant_missing_rule_class", "traces", "replay_hash",
    ):
        assert k in d
