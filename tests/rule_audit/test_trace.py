"""Tests for v2.5 RuleCoverageTrace + classifier (Aufgaben 2, 5)."""
from __future__ import annotations

from desi.rule_audit import (
    MissingRuleClass,
    classify_missing_rule,
    trace_replay_hash,
)


def test_no_loss_when_a_rule_matched() -> None:
    out = classify_missing_rule(
        matched_rule="syllogism",
        premise_count=2, premise_kinds=("universal", "particular"),
        text="All A are B. X is A. Therefore X is B.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.NONE


def test_cycle_structural_for_cycle_case() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=2, premise_kinds=("conditional", "conditional"),
        text="If P then Q. If Q then P.",
        expected_cycle=True,
    )
    assert out is MissingRuleClass.CYCLE_STRUCTURAL


def test_chained_conditional_when_multiple_conditionals() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=2,
        premise_kinds=("conditional", "conditional"),
        text="If A then B. If B then C. Therefore A then C.",
        expected_cycle=False,
    )
    assert out in (
        MissingRuleClass.CHAINED_CONDITIONAL,
        MissingRuleClass.MULTI_HOP_IMPLICATION,
    )


def test_multi_hop_implication_when_three_or_more_conditionals() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=3,
        premise_kinds=("implication", "implication", "implication"),
        text="If A then B. If B then C. If C then D. Therefore A then D.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.MULTI_HOP_IMPLICATION


def test_causal_chain_when_multiple_therefore() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=1, premise_kinds=("particular",),
        text="It rained. Therefore wet. Therefore slow.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.CAUSAL_CHAIN


def test_causal_chain_when_many_premises_one_therefore() -> None:
    """Implicit chain: 3+ sequential atomic premises + one conclusion."""
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=3,
        premise_kinds=("atomic", "atomic", "atomic"),
        text="Storm. Trees fell. Power gone. Therefore emergency.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.CAUSAL_CHAIN


def test_chained_temporal_when_temporal_markers_present() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=2, premise_kinds=("atomic", "atomic"),
        text="It rained. Then the street is wet.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.CHAINED_TEMPORAL


def test_unknown_when_no_structural_hint() -> None:
    out = classify_missing_rule(
        matched_rule=None,
        premise_count=1, premise_kinds=("atomic",),
        text="A floating sentence.",
        expected_cycle=False,
    )
    assert out is MissingRuleClass.UNKNOWN


def test_classifier_always_returns_enum_member() -> None:
    out = classify_missing_rule(
        matched_rule=None, premise_count=0, premise_kinds=(),
        text="", expected_cycle=False,
    )
    assert out in set(MissingRuleClass)


def test_classifier_is_deterministic() -> None:
    args = dict(
        matched_rule=None, premise_count=2,
        premise_kinds=("atomic", "atomic"),
        text="Storm. Power gone. Therefore emergency.",
        expected_cycle=False,
    )
    a = classify_missing_rule(**args)
    b = classify_missing_rule(**args)
    assert a is b


def test_replay_hash_is_deterministic() -> None:
    payload = {"case_id": "X", "premise_count": 2, "matched_rule": None}
    a = trace_replay_hash(payload)
    b = trace_replay_hash(payload)
    assert a == b
    assert len(a) == 16


def test_replay_hash_excludes_its_own_field() -> None:
    a = trace_replay_hash({"a": 1, "replay_hash": "x"})
    b = trace_replay_hash({"a": 1, "replay_hash": "y"})
    assert a == b
