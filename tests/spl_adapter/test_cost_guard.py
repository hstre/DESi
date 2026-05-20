"""Tests for the LLM cost guard — 20 ok, 21 blocked."""
from __future__ import annotations

import json

from desi.spl_adapter import (
    LLMSemanticBackend,
    LLM_PROJECTION_BUDGET,
    SPLAdapter,
)


def _ok_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.9, "ambiguous": False,
             "proposed_relations": []}
        ]
    })


# ---------------------------------------------------------------------------
# Budget constant
# ---------------------------------------------------------------------------


def test_default_budget_is_twenty() -> None:
    assert LLM_PROJECTION_BUDGET == 20


# ---------------------------------------------------------------------------
# 20 succeed, 21st fail-closes
# ---------------------------------------------------------------------------


def test_twenty_projections_all_yield_claims() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    for i in range(20):
        result = adapter.project_text(f"Water boils at 100C. (call {i})")
        assert len(result.claims) == 1, f"call {i} produced no claim"
        assert result.cost_guarded is False
    assert adapter.llm_calls_made == 20


def test_twenty_first_projection_is_cost_guarded() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    for _ in range(20):
        adapter.project_text("Water boils at 100C.")
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.cost_guarded is True
    assert adapter.llm_calls_made == 20  # NOT incremented when guarded


def test_cost_guard_remaining_counter() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    assert adapter.llm_calls_remaining == 20
    adapter.project_text("Water boils at 100C.")
    assert adapter.llm_calls_remaining == 19
    for _ in range(19):
        adapter.project_text("Water boils at 100C.")
    assert adapter.llm_calls_remaining == 0


def test_cost_guard_is_per_adapter_instance() -> None:
    """Two adapters share no cost-guard state."""
    a = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    b = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    for _ in range(20):
        a.project_text("Water boils at 100C.")
    # `a` is exhausted; `b` is fresh.
    result_a = a.project_text("Water boils at 100C.")
    result_b = b.project_text("Water boils at 100C.")
    assert result_a.cost_guarded is True
    assert result_b.cost_guarded is False
    assert len(result_b.claims) == 1


# ---------------------------------------------------------------------------
# Cost guard does not apply to the deterministic backend
# ---------------------------------------------------------------------------


def test_deterministic_backend_is_not_cost_guarded() -> None:
    adapter = SPLAdapter()
    for _ in range(50):
        result = adapter.project_text("Water boils at 100C.")
        assert result.cost_guarded is False
        assert len(result.claims) == 1


# ---------------------------------------------------------------------------
# Custom budget
# ---------------------------------------------------------------------------


def test_custom_budget_is_honoured() -> None:
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_ok_llm_call),
        llm_projection_budget=3,
    )
    for _ in range(3):
        result = adapter.project_text("Water boils at 100C.")
        assert result.cost_guarded is False
    result = adapter.project_text("Water boils at 100C.")
    assert result.cost_guarded is True
