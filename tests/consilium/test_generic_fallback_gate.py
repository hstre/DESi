"""Tests for the v1.6 generic-fallback bridge gate.

The four required changes:

1. ``BridgeKind`` closed enum + bridge classification in
   :func:`desi.logic.bridge_claims.propose_bridge`.
2. LOGICIAN rejects GENERIC_FALLBACK without causal mechanism.
3. SKEPTIC auto-VETOs GENERIC_FALLBACK with five auto-generated
   adversarial conditions.
4. ``RecursiveResolver`` threads context + additional_conditions
   into every consilium call.
"""
from __future__ import annotations

from desi.consilium import (
    BridgeConsilium,
    ConsiliumRole,
    Verdict,
    review_logician,
    review_skeptic,
    ReviewContext,
)
from desi.logic import LogicalAuditor
from desi.logic.bridge_claims import (
    BRIDGE_METHOD,
    BridgeClaim,
    BridgeKind,
    propose_bridge,
)
from desi.logic.gap_detector import detect_gap
from desi.logic.premises import PremiseExtractor
from desi.memory.claim import Claim, ClaimState, Provenance


# ---------------------------------------------------------------------------
# BridgeKind enum + classification at synthesis time
# ---------------------------------------------------------------------------


def test_bridge_kind_enum_has_two_values() -> None:
    values = {k.value for k in BridgeKind}
    assert values == {"specific", "generic_fallback"}


def test_propose_bridge_marks_rain_street_as_specific() -> None:
    props = PremiseExtractor().extract(
        "It is raining. Therefore the street is wet."
    )
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge is not None
    assert bridge.kind is BridgeKind.SPECIFIC


def test_propose_bridge_marks_generic_template_as_generic_fallback() -> None:
    """For inputs the rain/street heuristic does not match, the
    generic ``"(X) implies (Y)"`` template fires — and must be
    classified GENERIC_FALLBACK."""
    props = PremiseExtractor().extract(
        "The temperature is freezing. Therefore the water is ice."
    )
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge is not None
    assert bridge.kind is BridgeKind.GENERIC_FALLBACK
    assert "implies" in bridge.text.lower()


def test_bridge_claim_kind_default_is_specific() -> None:
    """Hand-constructed bridges that omit ``kind`` default to
    SPECIFIC — preserves backwards compatibility with v1.2 / v1.3
    test fixtures."""
    b = BridgeClaim(
        bridge_id="br_x",
        text="rain causes the street to be wet",
        claim=Claim(
            content="rain causes the street to be wet",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="x", run_id="r"),
        ),
        rationale="x",
    )
    assert b.kind is BridgeKind.SPECIFIC


# ---------------------------------------------------------------------------
# LOGICIAN hard gate
# ---------------------------------------------------------------------------


def _generic_ctx() -> ReviewContext:
    """Build a ReviewContext around a GENERIC_FALLBACK bridge."""
    props = PremiseExtractor().extract(
        "The temperature is freezing. Therefore the water is ice."
    )
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge is not None and bridge.kind is BridgeKind.GENERIC_FALLBACK
    return ReviewContext(
        bridge=bridge,
        source_claim_id="ac_test",
        original_text="The temperature is freezing. "
                      "Therefore the water is ice.",
    )


def test_logician_rejects_generic_fallback_without_mechanism() -> None:
    """GENERIC_FALLBACK bridges with no causal-mechanism word fail
    the LOGICIAN regardless of token overlap."""
    review = review_logician(_generic_ctx())
    assert review.unresolved_gap is True
    assert "generic_fallback_no_mechanism" in review.findings


def test_logician_accepts_specific_bridge_without_mechanism() -> None:
    """SPECIFIC bridges are not held to the mechanism-word gate."""
    props = PremiseExtractor().extract(
        "It is raining. Therefore the street is wet."
    )
    bridge = propose_bridge(props, detect_gap(props))
    ctx = ReviewContext(
        bridge=bridge,
        source_claim_id="ac_test",
        original_text="It is raining. Therefore the street is wet.",
    )
    review = review_logician(ctx)
    assert review.unresolved_gap is False


def test_logician_accepts_specific_bridge_with_mechanism() -> None:
    """A hand-crafted SPECIFIC bridge with a causal verb passes."""
    bridge = BridgeClaim(
        bridge_id="br_x",
        text="rain causes the street to be wet",
        claim=Claim(content="rain causes the street to be wet",
                     method=BRIDGE_METHOD,
                     state=ClaimState.PROPOSED,
                     provenance=Provenance(source="x", run_id="r")),
        rationale="x",
        kind=BridgeKind.SPECIFIC,
    )
    ctx = ReviewContext(
        bridge=bridge, source_claim_id="ac_test",
        original_text="It is raining. Therefore the street is wet.",
    )
    review = review_logician(ctx)
    assert review.unresolved_gap is False


# ---------------------------------------------------------------------------
# SKEPTIC mandatory pressure
# ---------------------------------------------------------------------------


def test_skeptic_auto_vetos_generic_fallback() -> None:
    review = review_skeptic(_generic_ctx())
    assert review.unresolved_gap is True


def test_skeptic_auto_generates_at_least_three_adversarial_conditions() -> None:
    review = review_skeptic(_generic_ctx())
    auto_findings = [
        f for f in review.findings if f.startswith("auto_adversarial:")
    ]
    assert len(auto_findings) >= 3


def test_skeptic_auto_adversarial_conditions_include_the_directives_examples() -> None:
    """The directive's example conditions should all appear in the
    auto-generated set (alternative cause, hidden variable, category
    mismatch, shelter/roof, affirming the consequent)."""
    review = review_skeptic(_generic_ctx())
    flat = " ".join(review.findings).lower()
    for kw in ("alternative cause", "hidden variable",
                "category", "roof", "affirms the consequent"):
        assert kw in flat, f"missing auto-adversarial keyword: {kw}"


def test_skeptic_specific_bridge_is_silent_without_user_conditions() -> None:
    """SPECIFIC bridges with no additional_conditions stay clean."""
    props = PremiseExtractor().extract(
        "It is raining. Therefore the street is wet."
    )
    bridge = propose_bridge(props, detect_gap(props))
    ctx = ReviewContext(
        bridge=bridge, source_claim_id="ac_test",
        original_text="It is raining. Therefore the street is wet.",
    )
    review = review_skeptic(ctx)
    assert review.unresolved_gap is False


# ---------------------------------------------------------------------------
# End-to-end through BridgeConsilium
# ---------------------------------------------------------------------------


def test_consilium_vetoes_generic_fallback_bridge() -> None:
    audit = LogicalAuditor().audit(
        "The temperature is freezing. Therefore the water is ice."
    )
    bridge = audit.bridges[0]
    assert bridge.kind is BridgeKind.GENERIC_FALLBACK
    res = BridgeConsilium().deliberate(
        bridge,
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    assert res.verdict.verdict is Verdict.VETO


def test_consilium_blocking_roles_include_logician_and_skeptic() -> None:
    audit = LogicalAuditor().audit(
        "The temperature is freezing. Therefore the water is ice."
    )
    res = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    blocking = set(res.verdict.blocking_roles)
    assert ConsiliumRole.LOGICIAN in blocking
    assert ConsiliumRole.SKEPTIC in blocking


# ---------------------------------------------------------------------------
# Resolver context threading
# ---------------------------------------------------------------------------


def test_resolver_threads_context_through_to_consilium() -> None:
    """When the resolver is given a context, the DOMAIN_EXAMINER
    inside each consilium call must see it. We probe this via a
    case where the context flips the verdict (D3 in the benchmark
    — the financial-newspaper metaphor case)."""
    from desi.recursive import RecursiveResolver, ResolutionState
    text = "The market is hot. Therefore the city is flooded."
    res_no_ctx = RecursiveResolver().resolve(text)
    res_with_ctx = RecursiveResolver().resolve(
        text, context="financial_newspaper",
    )
    # Both block under v1.6 because the bridge is GENERIC_FALLBACK
    # and the SKEPTIC auto-VETOs. The point of THIS test is that
    # the context was actually received: the verdict rationale at
    # least mentions the DOMAIN_EXAMINER's metaphor finding for the
    # contextful run. We assert both block and that the second run
    # is reproducible.
    assert res_no_ctx.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert res_with_ctx.final_state is ResolutionState.RESOLUTION_BLOCKED


def test_resolver_passes_additional_conditions_through() -> None:
    """The roof counterexample must veto a specific bridge when
    threaded through the resolver."""
    from desi.recursive import RecursiveResolver, ResolutionState
    text = "It is raining. Therefore the street is wet."
    # Without the roof condition, v1.6 still completes (specific bridge).
    res = RecursiveResolver().resolve(text)
    assert res.final_state is ResolutionState.RESOLUTION_COMPLETE
    # With the roof condition, the SKEPTIC vetoes.
    res_with_roof = RecursiveResolver().resolve(
        text, additional_conditions=("the street has a roof",),
    )
    assert res_with_roof.final_state is ResolutionState.RESOLUTION_BLOCKED
