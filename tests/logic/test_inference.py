"""Tests for v1.2 inference rules — closed enum of 5 validators."""
from __future__ import annotations

from desi.logic import (
    InferenceRule,
    LogicalAuditor,
    LogicalState,
    PremiseExtractor,
    try_each_rule,
    validate_inference,
)


def _ext() -> PremiseExtractor:
    return PremiseExtractor()


# ---------------------------------------------------------------------------
# Closed enum
# ---------------------------------------------------------------------------


def test_inference_rule_enum_has_exactly_six_members() -> None:
    """v2.7 added CAUSAL_CHAIN to the original v1.2 set of five."""
    members = {m.value for m in InferenceRule}
    assert members == {"syllogism", "implication", "transitivity",
                       "contradiction", "equivalence", "causal_chain"}


def test_inference_rule_value_uses_lowercase_underscore() -> None:
    for r in InferenceRule:
        assert r.value == r.value.lower()
        assert " " not in r.value


# ---------------------------------------------------------------------------
# P1 — syllogism
# ---------------------------------------------------------------------------


def test_p1_syllogism_matches() -> None:
    props = _ext().extract(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    match = try_each_rule(props)
    assert match is not None
    assert match.rule == InferenceRule.SYLLOGISM
    assert len(match.used_premise_ids) == 2


def test_syllogism_does_not_match_when_predicate_differs() -> None:
    props = _ext().extract(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is happy."
    )
    match = try_each_rule(props)
    assert match is None


# ---------------------------------------------------------------------------
# Implication (modus ponens)
# ---------------------------------------------------------------------------


def test_modus_ponens_matches() -> None:
    props = _ext().extract(
        "It rains. If it rains then the street is wet. "
        "Therefore the street is wet."
    )
    match = try_each_rule(props)
    assert match is not None
    assert match.rule == InferenceRule.IMPLICATION


# ---------------------------------------------------------------------------
# Transitivity
# ---------------------------------------------------------------------------


def test_transitivity_matches_when_chain_closes() -> None:
    props = _ext().extract("a -> b. b -> c. Therefore a -> c.")
    match = try_each_rule(props)
    assert match is not None
    assert match.rule == InferenceRule.TRANSITIVITY


def test_transitivity_does_not_match_with_wrong_consequent() -> None:
    props = _ext().extract("a -> b. b -> c. Therefore a -> d.")
    match = try_each_rule(props)
    assert match is None


# ---------------------------------------------------------------------------
# Contradiction
# ---------------------------------------------------------------------------


def test_contradiction_detects_p_and_not_p() -> None:
    props = _ext().extract(
        "Socrates is mortal. Socrates is not mortal. "
        "Therefore the premises contradict."
    )
    match = try_each_rule(props)
    assert match is not None
    assert match.rule == InferenceRule.CONTRADICTION


# ---------------------------------------------------------------------------
# validate_inference targets a specific rule
# ---------------------------------------------------------------------------


def test_validate_inference_returns_none_when_rule_does_not_match() -> None:
    props = _ext().extract("a -> b. b -> c. Therefore a -> d.")
    assert validate_inference(
        InferenceRule.TRANSITIVITY,
        props.premises, props.conclusion,
    ) is None


def test_validate_inference_returns_match_when_rule_applies() -> None:
    props = _ext().extract("a -> b. b -> c. Therefore a -> c.")
    m = validate_inference(
        InferenceRule.TRANSITIVITY,
        props.premises, props.conclusion,
    )
    assert m is not None and m.rule == InferenceRule.TRANSITIVITY


# ---------------------------------------------------------------------------
# Auditor wires all five validators in order
# ---------------------------------------------------------------------------


def test_auditor_returns_logically_supported_for_p1() -> None:
    r = LogicalAuditor().audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    assert r.state == LogicalState.LOGICALLY_SUPPORTED
    assert r.rule == InferenceRule.SYLLOGISM


def test_auditor_returns_logically_rejected_for_p5() -> None:
    r = LogicalAuditor().audit("a -> b. b -> c. Therefore a -> d.")
    assert r.state == LogicalState.LOGICALLY_REJECTED
