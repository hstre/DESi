"""Tests for v1.1 per-document cost guard — 5 projections per doc max."""
from __future__ import annotations

import json

from desi.spl_adapter import (
    LLMSemanticBackend,
    PER_DOCUMENT_PROJECTION_BUDGET,
    SourceDocument,
    SPLAdapter,
)


def _ok_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": "Water boils at 100C.",
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })


def _doc(document_id: str = "doc_1") -> SourceDocument:
    return SourceDocument(
        document_id=document_id, content="Water boils at 100C.",
        content_type="text/plain",
    )


# ---------------------------------------------------------------------------
# Budget constant
# ---------------------------------------------------------------------------


def test_per_document_budget_is_five() -> None:
    assert PER_DOCUMENT_PROJECTION_BUDGET == 5


# ---------------------------------------------------------------------------
# 5 succeed, 6th is fail-closed
# ---------------------------------------------------------------------------


def test_five_projections_of_one_document_all_admitted() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    doc = _doc("doc_a")
    for i in range(5):
        result = adapter.project_document(doc)
        assert len(result.claims) == 1, f"call {i}"
        assert result.cost_guarded is False
    assert adapter.projections_for_document("doc_a") == 5


def test_sixth_projection_of_same_document_is_cost_guarded() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    doc = _doc("doc_a")
    for _ in range(5):
        adapter.project_document(doc)
    result = adapter.project_document(doc)
    assert result.claims == ()
    assert result.cost_guarded is True
    # Counter does NOT increment on guard-fire (consistent with v1.0 contract).
    assert adapter.projections_for_document("doc_a") == 5


def test_per_document_budget_is_independent_across_documents() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    doc_a = _doc("doc_a")
    doc_b = _doc("doc_b")
    for _ in range(5):
        adapter.project_document(doc_a)
    # doc_a is exhausted; doc_b is fresh.
    r_a = adapter.project_document(doc_a)
    r_b = adapter.project_document(doc_b)
    assert r_a.cost_guarded is True
    assert r_b.cost_guarded is False
    assert len(r_b.claims) == 1


# ---------------------------------------------------------------------------
# Per-document guard does NOT apply to the deterministic backend
# ---------------------------------------------------------------------------


def test_deterministic_backend_is_not_per_document_guarded() -> None:
    adapter = SPLAdapter()
    doc = _doc("doc_a")
    for _ in range(20):
        result = adapter.project_document(doc)
        assert result.cost_guarded is False
        assert len(result.claims) == 1
    assert adapter.projections_for_document("doc_a") == 0  # det. is not tracked


# ---------------------------------------------------------------------------
# Per-document and per-adapter guards interact correctly
# ---------------------------------------------------------------------------


def test_per_adapter_budget_still_applies_across_documents() -> None:
    """5 docs × 5 calls = 25 attempts; per-adapter budget (20) caps total."""
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    admitted_count = 0
    for d in range(5):
        for _ in range(5):
            r = adapter.project_document(_doc(f"doc_{d}"))
            if len(r.claims) > 0:
                admitted_count += 1
    # Per-adapter budget is 20; the 21st call onward is cost_guarded
    # regardless of which document.
    assert admitted_count == 20


# ---------------------------------------------------------------------------
# project_text without a document_id is not per-doc tracked
# ---------------------------------------------------------------------------


def test_project_text_without_document_id_is_not_per_doc_tracked() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    for _ in range(10):
        result = adapter.project_text("Water boils at 100C.")
        assert result.cost_guarded is False
    # Per-doc counters are empty; only the per-adapter budget is used.
    assert adapter.projections_for_document("") == 0
