"""Tests for v2.5 RuleCoverageRunner (Aufgaben 3, 4)."""
from __future__ import annotations

from desi.benchmark_multistep import ALL_MULTISTEP_CASES
from desi.rule_audit import (
    AttemptedRule,
    MissingRuleClass,
    RuleCoverageRunner,
    RuleCoverageTrace,
)


def test_runner_traces_thirty_cases() -> None:
    run = RuleCoverageRunner().run()
    assert len(run.traces) == 30


def test_runner_covers_all_v23_case_ids() -> None:
    run = RuleCoverageRunner().run()
    ids = {t.case_id for t in run.traces}
    assert ids == {c.case_id for c in ALL_MULTISTEP_CASES}


def test_each_trace_is_a_RuleCoverageTrace() -> None:
    run = RuleCoverageRunner().run()
    for t in run.traces:
        assert isinstance(t, RuleCoverageTrace)


def test_attempted_rules_only_from_closed_enum() -> None:
    """Aufgabe 4: only the five known rules may appear."""
    enum_values = {r.value for r in AttemptedRule}
    run = RuleCoverageRunner().run()
    for t in run.traces:
        for r in t.attempted_rules:
            assert r in enum_values, (
                f"unknown rule probed by audit: {r!r}"
            )


def test_missing_rule_class_only_from_closed_enum() -> None:
    enum_values = {m.value for m in MissingRuleClass}
    run = RuleCoverageRunner().run()
    for t in run.traces:
        assert t.missing_rule_class.value in enum_values


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = RuleCoverageRunner().run()
    b = RuleCoverageRunner().run()
    for ta, tb in zip(a.traces, b.traces):
        assert ta.replay_hash == tb.replay_hash, ta.case_id


def test_two_runs_produce_identical_missing_rule_classes() -> None:
    a = RuleCoverageRunner().run()
    b = RuleCoverageRunner().run()
    for ta, tb in zip(a.traces, b.traces):
        assert ta.missing_rule_class is tb.missing_rule_class


def test_rule_attempts_equals_attempted_rules_length() -> None:
    run = RuleCoverageRunner().run()
    for t in run.traces:
        assert t.rule_attempts == len(t.attempted_rules)


def test_no_rule_match_consistent_with_matched_rule() -> None:
    run = RuleCoverageRunner().run()
    for t in run.traces:
        if t.matched_rule is None:
            # matched_rule None doesn't imply no_rule_match=True
            # because v1.2's auditor may set rule=None even when
            # validate_inference would match. They are independent
            # observations; we only assert the inverse direction:
            pass
        else:
            assert t.no_rule_match is False, t.case_id


def test_premise_count_nonnegative() -> None:
    run = RuleCoverageRunner().run()
    for t in run.traces:
        assert t.premise_count >= 0


def test_to_dict_round_trip_shape() -> None:
    run = RuleCoverageRunner().run()
    d = run.traces[0].to_dict()
    for k in (
        "case_id", "category", "premise_count", "premise_kinds",
        "conclusion_kind", "parser_recognized", "audit_state",
        "matched_rule", "rule_attempts", "attempted_rules",
        "no_rule_match", "bridge_created", "bridge_kind",
        "final_state", "blocking_reason", "missing_rule_class",
        "replay_hash",
    ):
        assert k in d
