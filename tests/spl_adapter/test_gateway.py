"""Tests for SPLGateway — the only path text → DESi Claim.

The v1.0 directive: direct text → Claim construction is forbidden.
The gateway is the only place where a ClaimCandidate becomes a Claim,
and it filters by a closed rejection taxonomy.
"""
from __future__ import annotations

import pytest

from desi.spl_adapter import (
    ClaimCandidate,
    GatewayRejection,
    SPLAdapter,
    SPLGateway,
    candidate_to_claim,
    make_deterministic_provenance,
    make_llm_provenance,
)


# ---------------------------------------------------------------------------
# Mapping refuses to bypass the gateway
# ---------------------------------------------------------------------------


def test_candidate_to_claim_refuses_empty_content() -> None:
    cand = ClaimCandidate(
        content="", method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
    )
    with pytest.raises(GatewayRejection) as exc:
        candidate_to_claim(cand, run_id="run_x")
    assert exc.value.reason == "empty_content"


def test_candidate_to_claim_refuses_unknown_method() -> None:
    cand = ClaimCandidate(
        content="water boils at 100°C", method="hearsay",
        spl_provenance=make_deterministic_provenance(),
    )
    with pytest.raises(GatewayRejection) as exc:
        candidate_to_claim(cand, run_id="run_x")
    assert exc.value.reason == "invalid_method"


# ---------------------------------------------------------------------------
# Gateway rejection rules — closed taxonomy
# ---------------------------------------------------------------------------


def test_gateway_rejects_ambiguous_candidate() -> None:
    cand = ClaimCandidate(
        content="water boils at 100°C",
        method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
        ambiguous=True, confidence=0.4,
    )
    admitted, rejected = SPLGateway().admit((cand,), run_id="run_x")
    assert admitted == ()
    assert rejected[0][1] == "ambiguous_claim"


def test_gateway_rejects_candidate_below_confidence_floor() -> None:
    cand = ClaimCandidate(
        content="water boils at 100°C",
        method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
        ambiguous=False, confidence=0.3,
    )
    _, rejected = SPLGateway().admit((cand,), run_id="run_x")
    assert rejected[0][1] == "ambiguous_claim"


def test_gateway_rejects_hallucinated_relation() -> None:
    cand = ClaimCandidate(
        content="water boils at 100°C",
        method="llm_semantic_projection",
        spl_provenance=make_llm_provenance(
            model_name="deepseek-4-pro", model_version="2026-05",
            prompt="p", output="o", temperature=0.0, max_tokens=64,
        ),
        proposed_relations=(
            ("water_boils", "SUPPORTS", "experimental_evidence"),
        ),
    )
    _, rejected = SPLGateway().admit((cand,), run_id="run_x")
    assert rejected[0][1] == "hallucinated_relation"


def test_gateway_admits_clean_candidate() -> None:
    cand = ClaimCandidate(
        content="water boils at 100°C",
        method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
        confidence=0.9, ambiguous=False,
    )
    admitted, rejected = SPLGateway().admit((cand,), run_id="run_x")
    assert len(admitted) == 1
    assert rejected == ()


# ---------------------------------------------------------------------------
# Adapter end-to-end
# ---------------------------------------------------------------------------


def test_adapter_returns_tuple_of_claim_objects_not_strings() -> None:
    from desi.memory.claim import Claim
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.")
    assert isinstance(result.claims, tuple)
    for c in result.claims:
        assert isinstance(c, Claim)


def test_adapter_reports_rejected_candidates() -> None:
    """Ambiguous input produces zero claims and one rejected pair."""
    adapter = SPLAdapter()
    result = adapter.project_text(
        "Water might possibly boil somewhere around 100 degrees."
    )
    assert result.claims == ()
    assert len(result.rejected) == 1
    cand, reason = result.rejected[0]
    assert reason == "ambiguous_claim"


def test_adapter_assigns_a_run_id_when_caller_omits_it() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.")
    assert all(c.provenance.run_id for c in result.claims)


def test_adapter_uses_caller_provided_run_id() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.", run_id="run_abc")
    for c in result.claims:
        assert c.provenance.run_id == "run_abc"
