"""Tests for fail-closed behaviour — every error path yields zero claims."""
from __future__ import annotations

import json

from desi.spl_adapter import (
    BackendError,
    LLMSemanticBackend,
    SPLAdapter,
)


# ---------------------------------------------------------------------------
# Backend exceptions are converted into zero claims + a ledger event
# ---------------------------------------------------------------------------


def test_api_timeout_yields_zero_claims() -> None:
    def _raise_timeout(prompt: str) -> str:
        raise TimeoutError("network timeout")

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_raise_timeout))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error  # non-empty kind
    assert result.cost_guarded is False


def test_connection_error_yields_zero_claims() -> None:
    def _raise_conn(prompt: str) -> str:
        raise ConnectionError("connection refused")

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_raise_conn))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "llm_call_failed"


# ---------------------------------------------------------------------------
# Malformed LLM output → zero claims
# ---------------------------------------------------------------------------


def test_invalid_json_output_yields_zero_claims() -> None:
    def _bad_json(prompt: str) -> str:
        return "not actually json"

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_bad_json))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "invalid_json"


def test_empty_output_yields_zero_claims() -> None:
    def _empty(prompt: str) -> str:
        return ""

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_empty))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "empty_output"


def test_missing_units_key_yields_zero_claims() -> None:
    def _wrong_schema(prompt: str) -> str:
        return json.dumps({"results": []})  # wrong key

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_wrong_schema))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "invalid_schema"


def test_units_is_not_a_list_yields_zero_claims() -> None:
    def _wrong_type(prompt: str) -> str:
        return json.dumps({"units": "should-be-a-list"})

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_wrong_type))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == "invalid_schema"


# ---------------------------------------------------------------------------
# Backend returns no units → still fail-closed, no claims, no exception
# ---------------------------------------------------------------------------


def test_empty_unit_list_yields_zero_claims_no_exception() -> None:
    def _empty_units(prompt: str) -> str:
        return json.dumps({"units": []})

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_empty_units))
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
    assert result.backend_error == ""  # not an error, just no output
    assert result.candidates_seen == 0


# ---------------------------------------------------------------------------
# The adapter swallows backend errors — they never propagate
# ---------------------------------------------------------------------------


def test_adapter_does_not_propagate_backend_errors() -> None:
    """The adapter is the boundary between fragile NLP and the rest
    of DESi; backend errors stay inside the adapter."""
    def _crash(prompt: str) -> str:
        raise RuntimeError("kaboom")

    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_crash))
    # No assertion on raise — the test passes if the call completes.
    result = adapter.project_text("Water boils at 100C.")
    assert result.claims == ()
