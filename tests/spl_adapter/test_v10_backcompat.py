"""Tests for v1.0 backwards compatibility — project_text still works."""
from __future__ import annotations

import json

from desi.spl_adapter import (
    LLMSemanticBackend,
    SPLAdapter,
    SourceDocument,
)


def _ok_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": "Water boils at 100C.",
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })


# ---------------------------------------------------------------------------
# v1.0 entry point still works without a SourceDocument
# ---------------------------------------------------------------------------


def test_project_text_still_works_with_deterministic_backend() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
    assert result.claims[0].content == "water boils at 100°C"
    assert result.claims[0].method == "deterministic_semantic_projection"


def test_project_text_still_works_with_llm_backend() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
    assert result.claims[0].method == "llm_semantic_projection"


def test_v10_signature_unchanged() -> None:
    """`project_text(text)` and `project_text(text, run_id=…)` must
    still accept exactly the kwargs they did in v1.0."""
    adapter = SPLAdapter()
    a = adapter.project_text("Water boils at 100C.")
    b = adapter.project_text("Water boils at 100C.", run_id="run_v10")
    assert len(a.claims) == 1
    assert len(b.claims) == 1
    assert b.claims[0].provenance.run_id == "run_v10"


# ---------------------------------------------------------------------------
# Same content via project_text and project_document yields claims with
# the same content + method
# ---------------------------------------------------------------------------


def test_project_text_and_project_document_agree_on_content() -> None:
    adapter = SPLAdapter()
    a = adapter.project_text("Water boils at 100C.", run_id="run_x")
    doc = SourceDocument(document_id="d_x", content="Water boils at 100C.",
                         content_type="text/plain")
    b = adapter.project_document(doc, run_id="run_x")
    assert a.claims[0].content == b.claims[0].content
    assert a.claims[0].method == b.claims[0].method
    # Same content + method + run_id → same claim_id.
    assert a.claims[0].claim_id == b.claims[0].claim_id


# ---------------------------------------------------------------------------
# v1.0 cost-guard surface still works (per-adapter budget)
# ---------------------------------------------------------------------------


def test_v10_per_adapter_budget_is_unchanged() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    assert adapter.llm_calls_remaining == 20
    for _ in range(20):
        adapter.project_text("Water boils at 100C.")
    assert adapter.llm_calls_remaining == 0
    result = adapter.project_text("Water boils at 100C.")
    assert result.cost_guarded is True
