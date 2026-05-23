"""Tests for the 50 KB response-size guard inside LLMSemanticBackend.

The guard is enforced at two layers:

1. :class:`DeepSeekClient` — the HTTP transport refuses oversized
   bodies (tested in test_deepseek_client.py).
2. :class:`LLMSemanticBackend._parse_response` — the parser also
   enforces the cap so that any injected ``llm_call`` (including
   non-DeepSeek transports) cannot smuggle in an oversized blob.

This file covers the second layer.
"""
from __future__ import annotations

import json

from desi.spl_adapter import (
    LLMSemanticBackend,
    MAX_LLM_RESPONSE_BYTES,
    SPLAdapter,
)


def _giant_llm_call(prompt: str) -> str:
    """Return a syntactically-valid JSON body that exceeds 50 KB."""
    filler = "x" * (MAX_LLM_RESPONSE_BYTES + 1024)
    return json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": filler,
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })


def test_response_too_large_fail_closes() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_giant_llm_call))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "response_too_large"


def _ok_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": "Water boils at 100C.",
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })


def test_response_under_limit_passes() -> None:
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_ok_llm_call))
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1


def test_response_at_limit_is_accepted() -> None:
    """A response exactly at the 50 KB cap passes through."""
    # Build a units list whose total JSON size is just under the cap.
    target = MAX_LLM_RESPONSE_BYTES - 200
    raw_span = "y" * target
    body = json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": raw_span,
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })
    assert len(body.encode("utf-8")) <= MAX_LLM_RESPONSE_BYTES

    def _at_limit_call(prompt: str) -> str:
        return body

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_at_limit_call))
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
