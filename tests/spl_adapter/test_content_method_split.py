"""Tests for the S7-equivalent invariant — same content, different method."""
from __future__ import annotations

import json

from desi.spl_adapter import (
    DeterministicSemanticBackend,
    LLMSemanticBackend,
    SPLAdapter,
)


def _llm_call_returning_water_boils(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.9, "ambiguous": False,
             "proposed_relations": []}
        ]
    })


# ---------------------------------------------------------------------------
# Two claims with identical content but different methods stay distinct
# ---------------------------------------------------------------------------


def test_deterministic_and_llm_produce_distinct_claim_ids() -> None:
    det_adapter = SPLAdapter()
    llm_adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_llm_call_returning_water_boils),
    )
    det_result = det_adapter.project_text(
        "Water boils at 100C.", run_id="run_shared",
    )
    llm_result = llm_adapter.project_text(
        "Water boils at 100C.", run_id="run_shared",
    )
    assert len(det_result.claims) == 1
    assert len(llm_result.claims) == 1
    det_claim = det_result.claims[0]
    llm_claim = llm_result.claims[0]
    # Same content...
    assert det_claim.content == llm_claim.content
    # Different methods...
    assert det_claim.method != llm_claim.method
    assert det_claim.method == "deterministic_semantic_projection"
    assert llm_claim.method == "llm_semantic_projection"
    # ...therefore distinct claim_ids (S7 invariant).
    assert det_claim.claim_id != llm_claim.claim_id


def test_method_is_one_of_two_legal_values() -> None:
    from desi.spl_adapter import LEGAL_METHODS
    assert LEGAL_METHODS == frozenset({
        "deterministic_semantic_projection",
        "llm_semantic_projection",
    })


def test_state_is_always_proposed_for_deterministic_backend() -> None:
    from desi.memory.claim import ClaimState
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.")
    for c in result.claims:
        assert c.state == ClaimState.PROPOSED


def test_state_is_always_proposed_for_llm_backend() -> None:
    from desi.memory.claim import ClaimState
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_llm_call_returning_water_boils),
    )
    result = adapter.project_text("Water boils at 100C.")
    for c in result.claims:
        assert c.state == ClaimState.PROPOSED


# ---------------------------------------------------------------------------
# A hand-crafted candidate with the SAME content but a different method
# tag also yields a different claim_id (the mapping never collapses).
# ---------------------------------------------------------------------------


def test_candidate_to_claim_respects_method_in_identity() -> None:
    from desi.spl_adapter import (
        ClaimCandidate,
        candidate_to_claim,
        make_deterministic_provenance,
        make_llm_provenance,
    )
    det_cand = ClaimCandidate(
        content="water boils at 100°C",
        method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
    )
    llm_cand = ClaimCandidate(
        content="water boils at 100°C",
        method="llm_semantic_projection",
        spl_provenance=make_llm_provenance(
            model_name="deepseek-4-pro", model_version="2026-05",
            prompt="p", output="o", temperature=0.0, max_tokens=64,
        ),
    )
    det_claim = candidate_to_claim(det_cand, run_id="run_shared")
    llm_claim = candidate_to_claim(llm_cand, run_id="run_shared")
    assert det_claim.claim_id != llm_claim.claim_id
