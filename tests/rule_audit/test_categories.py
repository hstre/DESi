"""Tests for v2.5 closed category enums (Aufgaben 4, 5)."""
from __future__ import annotations

from desi.logic.inference import InferenceRule
from desi.rule_audit import AttemptedRule, MissingRuleClass


_EXPECTED_ATTEMPTED = {
    "syllogism", "implication", "transitivity",
    "contradiction", "equivalence",
}


_EXPECTED_MISSING = {
    "none", "causal_chain", "multi_hop_implication",
    "chained_temporal", "chained_conditional",
    "cycle_structural", "unknown",
}


def test_attempted_rule_has_five_values() -> None:
    assert len(list(AttemptedRule)) == 5


def test_attempted_rule_matches_directive() -> None:
    assert {r.value for r in AttemptedRule} == _EXPECTED_ATTEMPTED


def test_attempted_rule_mirrors_v1_2_inference_rule() -> None:
    """AttemptedRule must list the exact same five rules that the
    v1.2 InferenceRule already exports — no new rules added."""
    assert {r.value for r in AttemptedRule} == {
        r.value for r in InferenceRule
    }


def test_missing_rule_class_has_seven_values() -> None:
    assert len(list(MissingRuleClass)) == 7


def test_missing_rule_class_set_matches_directive() -> None:
    assert {m.value for m in MissingRuleClass} == _EXPECTED_MISSING


def test_each_directive_name_present() -> None:
    for name in (
        "NONE", "CAUSAL_CHAIN", "MULTI_HOP_IMPLICATION",
        "CHAINED_TEMPORAL", "CHAINED_CONDITIONAL",
        "CYCLE_STRUCTURAL", "UNKNOWN",
    ):
        assert hasattr(MissingRuleClass, name), name


def test_attempted_rule_str_compatible() -> None:
    assert isinstance(AttemptedRule.SYLLOGISM.value, str)


def test_missing_rule_class_str_compatible() -> None:
    assert isinstance(MissingRuleClass.NONE.value, str)
