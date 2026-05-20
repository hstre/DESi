"""Tests for the v2.7 InferenceRule.CAUSAL_CHAIN — rule body + guards."""
from __future__ import annotations

from desi.logic import LogicalAuditor
from desi.logic.inference import (
    InferenceRule,
    try_each_rule,
    validate_inference,
)


# ---------------------------------------------------------------------------
# Aufgabe 1 — enum membership
# ---------------------------------------------------------------------------


def test_causal_chain_is_in_inference_rule_enum() -> None:
    assert "causal_chain" in {m.value for m in InferenceRule}


def test_inference_rule_now_has_six_members() -> None:
    assert len(list(InferenceRule)) == 6


# ---------------------------------------------------------------------------
# Aufgabe 4 — rule body fires on linear cause-effect chains
# ---------------------------------------------------------------------------


def _resolve_with_rule(text: str):
    aud = LogicalAuditor()
    r = aud.audit(text)
    return r.state.value, r.rule.value if r.rule else None


def test_three_step_chain_resolves_with_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "It rained. The street is wet. Traffic slowed down. "
        "Therefore the delivery arrived late."
    )
    assert state == "logically_supported"
    assert rule == "causal_chain"


def test_four_step_chain_resolves_with_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "A storm arrived. Trees fell. Power lines snapped. "
        "Houses lost power. Therefore an emergency was declared."
    )
    assert state == "logically_supported"
    assert rule == "causal_chain"


# ---------------------------------------------------------------------------
# Aufgabe 2 — Guard 1: CONTRADICTION-FIRST via dict ordering
# ---------------------------------------------------------------------------


def test_contradiction_rule_runs_before_causal_chain() -> None:
    """A premise set the v1.2 contradiction rule already matches
    must produce a CONTRADICTION verdict, not a CAUSAL_CHAIN one."""
    state, rule = _resolve_with_rule(
        "Socrates is mortal. Socrates is not mortal. "
        "Therefore the premises contradict."
    )
    assert rule == "contradiction"


def test_negation_marker_in_premise_blocks_causal_chain() -> None:
    """Negation in any premise text refuses the chain."""
    state, rule = _resolve_with_rule(
        "It rained. The street is not wet. Traffic slowed down. "
        "Therefore the delivery arrived late."
    )
    assert rule != "causal_chain"


def test_negation_marker_in_conclusion_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "It rained. The street is wet. Traffic slowed down. "
        "Therefore the delivery did not arrive."
    )
    assert rule != "causal_chain"


# ---------------------------------------------------------------------------
# Aufgabe 3 — Guard 2: cycle delegation
# ---------------------------------------------------------------------------


def test_cycle_connective_because_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "I trust him because she trusts him. "
        "She trusts him because I trust him. "
        "Therefore trust is established."
    )
    assert rule != "causal_chain"


def test_cycle_connective_depends_on_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "A depends on B. B depends on C. C depends on A. "
        "Therefore A is established."
    )
    assert rule != "causal_chain"


def test_cycle_connective_relies_on_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "The proof relies on the lemma. "
        "The lemma relies on the theorem. "
        "The theorem relies on the proof. Therefore the proof is sound."
    )
    assert rule != "causal_chain"


def test_token_repetition_3_premises_blocks_causal_chain() -> None:
    """A content token appearing in three or more premises is a
    structural cycle — defer to cycle resolution."""
    state, rule = _resolve_with_rule(
        "Definition A uses material X. "
        "Definition B uses material X. "
        "Definition C uses material X. "
        "Therefore X is consumed."
    )
    assert rule != "causal_chain"


# ---------------------------------------------------------------------------
# Aufgabe 4 — additional negative cases the guards must block
# ---------------------------------------------------------------------------


def test_universal_premise_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "All birds fly. Penguins are birds. Penguins are flightless. "
        "Therefore penguins fly."
    )
    assert rule != "causal_chain"


def test_quantifier_some_blocks_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "Some cats are black. The cat is on the mat. "
        "Therefore the mat is black."
    )
    assert rule != "causal_chain"


def test_recycled_conclusion_token_blocks_causal_chain() -> None:
    """Light travels in straight lines. Lenses bend light. Therefore
    light bends in straight lines — conclusion content tokens
    appear in 2+ premises."""
    state, rule = _resolve_with_rule(
        "Light travels in straight lines. Lenses bend light. "
        "Therefore light bends in straight lines."
    )
    assert rule != "causal_chain"


def test_single_premise_does_not_trigger_causal_chain() -> None:
    state, rule = _resolve_with_rule(
        "It rained. Therefore the street is wet."
    )
    assert rule != "causal_chain"


# ---------------------------------------------------------------------------
# Aufgabe 7 — replay determinism
# ---------------------------------------------------------------------------


def test_replay_same_premises_same_match_across_two_runs() -> None:
    text = (
        "It rained. The street is wet. Traffic slowed down. "
        "Therefore the delivery arrived late."
    )
    aud_a = LogicalAuditor()
    aud_b = LogicalAuditor()
    ra = aud_a.audit(text)
    rb = aud_b.audit(text)
    assert ra.state.value == rb.state.value
    assert (ra.rule.value if ra.rule else None) == (
        rb.rule.value if rb.rule else None
    )
    # Premise ids canonicalise on text — same text → same ids.
    assert ra.propositions.premise_ids == rb.propositions.premise_ids


# ---------------------------------------------------------------------------
# Direct validator API
# ---------------------------------------------------------------------------


def test_validate_inference_dispatches_to_causal_chain() -> None:
    """The public single-rule entry point accepts the new rule."""
    aud = LogicalAuditor()
    r = aud.audit(
        "It rained. The street is wet. Traffic slowed down. "
        "Therefore the delivery arrived late."
    )
    match = validate_inference(
        InferenceRule.CAUSAL_CHAIN,
        r.propositions.premises,
        r.propositions.conclusion,
    )
    assert match is not None
    assert match.rule is InferenceRule.CAUSAL_CHAIN


def test_try_each_rule_returns_causal_chain_only_after_others_fail() -> None:
    """The other five rules must not match on a chain text."""
    aud = LogicalAuditor()
    r = aud.audit(
        "It rained. The street is wet. Traffic slowed down. "
        "Therefore the delivery arrived late."
    )
    props = r.propositions
    # The four non-CAUSAL rules must all return None.
    for rule in (
        InferenceRule.SYLLOGISM, InferenceRule.IMPLICATION,
        InferenceRule.TRANSITIVITY, InferenceRule.CONTRADICTION,
        InferenceRule.EQUIVALENCE,
    ):
        m = validate_inference(rule, props.premises, props.conclusion)
        assert m is None, f"{rule.value} unexpectedly matched a chain"
    # CAUSAL_CHAIN matches.
    m = validate_inference(
        InferenceRule.CAUSAL_CHAIN, props.premises, props.conclusion,
    )
    assert m is not None
    # And try_each_rule returns the same result.
    overall = try_each_rule(props)
    assert overall is not None
    assert overall.rule is InferenceRule.CAUSAL_CHAIN
