"""Tests for v1.3 counterexample + metaphor library — closed pattern sets."""
from __future__ import annotations

from desi.consilium import (
    BridgeConsilium,
    Verdict,
    find_counterexample,
    find_metaphor,
    supported_contexts,
)


# ---------------------------------------------------------------------------
# Counterexample matcher — direct API
# ---------------------------------------------------------------------------


def test_roof_negates_exposed_to_the_rain() -> None:
    hit = find_counterexample(
        "the street is exposed to the rain",
        ("the street has a roof",),
    )
    assert hit is not None
    assert "roof" in hit.pattern


def test_sheltered_negates_exposed_to_the_rain() -> None:
    hit = find_counterexample(
        "the street is exposed to the rain",
        ("the street is sheltered by an awning",),
    )
    assert hit is not None
    assert "sheltered" in hit.pattern


def test_no_negator_returns_none() -> None:
    hit = find_counterexample(
        "the street is exposed to the rain",
        ("the street is paved with asphalt",),
    )
    assert hit is None


def test_empty_conditions_returns_none() -> None:
    hit = find_counterexample(
        "the street is exposed to the rain", (),
    )
    assert hit is None


def test_matcher_is_deterministic_across_calls() -> None:
    a = find_counterexample(
        "the street is exposed to the rain",
        ("the street has a roof",),
    )
    b = find_counterexample(
        "the street is exposed to the rain",
        ("the street has a roof",),
    )
    assert a == b


# ---------------------------------------------------------------------------
# Metaphor library — direct API
# ---------------------------------------------------------------------------


def test_flooded_in_financial_context_is_metaphor() -> None:
    hit = find_metaphor(
        "the city is flooded after the announcement",
        "financial_newspaper",
    )
    assert hit is not None
    assert hit.word == "flooded"


def test_flooded_with_no_context_is_not_metaphor() -> None:
    hit = find_metaphor("the city is flooded", "")
    assert hit is None


def test_unknown_context_returns_none() -> None:
    hit = find_metaphor("the city is flooded", "ancient_poetry")
    assert hit is None


def test_supported_contexts_lists_at_least_two() -> None:
    ctxs = supported_contexts()
    assert "financial_newspaper" in ctxs
    assert len(ctxs) >= 2


# ---------------------------------------------------------------------------
# End-to-end: BridgeConsilium honours the libraries
# ---------------------------------------------------------------------------


def test_consilium_blocks_on_roof_counterexample() -> None:
    from desi.logic import LogicalAuditor
    aud = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    res = BridgeConsilium().deliberate(
        aud.bridges[0],
        source_claim_id=aud.audit_id,
        original_text=aud.text,
        additional_conditions=("the street has a roof",),
    )
    assert res.verdict.verdict is Verdict.VETO


def test_consilium_returns_needs_more_premises_on_metaphor_context() -> None:
    """v1.6 strengthening: the auto-generated bridge for the
    'The market is hot. Therefore the city is flooded.' input is
    :class:`BridgeKind.GENERIC_FALLBACK`. The v1.6 SKEPTIC and
    LOGICIAN both auto-VETO it. To exercise the NEEDS_MORE_PREMISES
    code path under v1.6, we hand-construct a SPECIFIC bridge that
    carries an explicit causal mechanism word — then only the
    DOMAIN_EXAMINER's metaphor flag remains active, and the
    aggregate verdict is NEEDS_MORE_PREMISES.
    """
    from desi.logic.bridge_claims import (
        BRIDGE_METHOD, BridgeClaim, BridgeKind,
    )
    from desi.memory.claim import Claim, ClaimState, Provenance
    text = "The market is hot. Therefore the city is flooded."
    # Specific bridge with an explicit causal verb so it survives
    # the v1.6 generic-fallback gate.
    specific_bridge = BridgeClaim(
        bridge_id="br_market_hot_specific",
        text="market heat causes the city flood",
        claim=Claim(
            content="market heat causes the city flood",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="test", run_id="r1"),
        ),
        rationale="hand-crafted specific bridge for metaphor test",
        kind=BridgeKind.SPECIFIC,
    )
    res = BridgeConsilium().deliberate(
        specific_bridge,
        source_claim_id="ac_test",
        original_text=text,
        context="financial_newspaper",
    )
    assert res.verdict.verdict is Verdict.NEEDS_MORE_PREMISES
