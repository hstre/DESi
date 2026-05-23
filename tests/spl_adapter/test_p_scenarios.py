"""P1–P4 — the four mandatory SPL evaluation scenarios.

* **P1 Paraphrase**: two phrasings of the same fact must produce the
  same canonical content (single semantic proposition).
* **P2 Same content, different method**: two backends emitting the
  identical canonical proposition must NOT be merged — distinct
  claim_ids are mandatory.
* **P3 Ambiguous claim**: hedge-language input must be rejected by
  the gateway, never admitted.
* **P4 Hallucinated relation**: an LLM that proposes a SUPPORTS /
  CONTRADICTS / MERGED_INTO edge must be blocked by the gateway —
  relations are DESi's responsibility, not the SPL's.
"""
from __future__ import annotations

import json

from desi.spl_adapter import (
    LLMSemanticBackend,
    SPLAdapter,
)


# ---------------------------------------------------------------------------
# P1 — Paraphrase
# ---------------------------------------------------------------------------


def test_p1_paraphrase_maps_to_same_canonical_content() -> None:
    adapter = SPLAdapter()
    a = adapter.project_text("Water boils at 100C.")
    b = adapter.project_text(
        "At one atmosphere water reaches boiling point at 100 degrees."
    )
    assert len(a.claims) == 1
    assert len(b.claims) == 1
    assert a.claims[0].content == b.claims[0].content


def test_p1_paraphrase_with_same_run_id_yields_same_claim_id() -> None:
    """Same content + same method + same run_id → same claim_id."""
    adapter = SPLAdapter()
    a = adapter.project_text("Water boils at 100C.", run_id="run_p1")
    b = adapter.project_text(
        "At one atmosphere water reaches boiling point at 100 degrees.",
        run_id="run_p1",
    )
    assert a.claims[0].claim_id == b.claims[0].claim_id


# ---------------------------------------------------------------------------
# P2 — Same content, different method
# ---------------------------------------------------------------------------


def _llm_returning_water_boils(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.9, "ambiguous": False,
             "proposed_relations": []}
        ]
    })


def test_p2_same_content_different_method_yields_two_claims() -> None:
    det = SPLAdapter()
    llm = SPLAdapter(backend=LLMSemanticBackend(
        llm_call=_llm_returning_water_boils,
    ))
    r_det = det.project_text("Water boils at 100C.", run_id="run_p2")
    r_llm = llm.project_text("Water boils at 100C.", run_id="run_p2")
    assert r_det.claims[0].content == r_llm.claims[0].content
    assert r_det.claims[0].method != r_llm.claims[0].method
    assert r_det.claims[0].claim_id != r_llm.claims[0].claim_id


# ---------------------------------------------------------------------------
# P3 — Ambiguous claim → gateway reject
# ---------------------------------------------------------------------------


def test_p3_ambiguous_input_produces_no_claim() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text(
        "Water might possibly boil somewhere around 100 degrees."
    )
    assert result.claims == ()


def test_p3_ambiguous_input_records_rejection() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text(
        "Maybe water boils at 100C. It is uncertain."
    )
    assert result.claims == ()
    reasons = [r for (_, r) in result.rejected]
    assert "ambiguous_claim" in reasons


# ---------------------------------------------------------------------------
# P4 — LLM proposes a SUPPORTS relation → gateway block
# ---------------------------------------------------------------------------


def _llm_proposing_supports_relation(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.95, "ambiguous": False,
             "proposed_relations": [
                 ["water_boils_at_100", "SUPPORTS", "experimental_evidence"]
             ]}
        ]
    })


def test_p4_llm_proposed_relation_is_blocked() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(
        llm_call=_llm_proposing_supports_relation,
    ))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    reasons = [r for (_, r) in result.rejected]
    assert "hallucinated_relation" in reasons


def _llm_proposing_contradicts_relation(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.95, "ambiguous": False,
             "proposed_relations": [
                 ["claim_a", "CONTRADICTS", "claim_b"]
             ]}
        ]
    })


def test_p4_contradicts_relation_also_blocked() -> None:
    """Any non-empty proposed_relations triggers the block, regardless
    of relation type. v1.0 forbids the SPL from proposing relations
    at all — only DESi may emit CONTRADICTS / MERGED_INTO / SUPPORTS
    edges through its own audited operators."""
    adapter = SPLAdapter(backend=LLMSemanticBackend(
        llm_call=_llm_proposing_contradicts_relation,
    ))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert "hallucinated_relation" in [r for (_, r) in result.rejected]


def test_p4_blocked_relation_does_not_consume_cost_budget_twice() -> None:
    """The cost guard tracks LLM calls, not gateway admissions."""
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(
            llm_call=_llm_proposing_supports_relation,
        ),
        llm_projection_budget=3,
    )
    for _ in range(3):
        adapter.project_text("Water boils at 100C.")
    # All three calls were made (claims were rejected, but budget was spent).
    assert adapter.llm_calls_made == 3
    result = adapter.project_text("Water boils at 100C.")
    assert result.cost_guarded is True
