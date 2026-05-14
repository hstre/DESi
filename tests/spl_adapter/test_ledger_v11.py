"""Tests for the 5 new v1.1 ledger event types."""
from __future__ import annotations

import json
import pathlib

import pytest

from desi.evolution import EvolutionLedger, EvolutionLedgerJSONL, LedgerEventType
from desi.spl_adapter import (
    DeepSeekClient,
    LLMSemanticBackend,
    SourceDocument,
    SPLAdapter,
)
from desi.spl_adapter.deepseek_client import API_KEY_ENV_VAR


# ---------------------------------------------------------------------------
# Enum membership
# ---------------------------------------------------------------------------


def test_five_v11_events_in_enum() -> None:
    values = {e.value for e in LedgerEventType}
    for expected in (
        "source_document_parsed",
        "llm_request_started",
        "llm_request_failed",
        "llm_response_accepted",
        "llm_response_rejected",
    ):
        assert expected in values


def test_v10_events_still_present() -> None:
    values = {e.value for e in LedgerEventType}
    for v in ("semantic_projection_started",
              "semantic_candidate_emitted",
              "semantic_projection_rejected"):
        assert v in values


# ---------------------------------------------------------------------------
# project_document emits SOURCE_DOCUMENT_PARSED
# ---------------------------------------------------------------------------


def test_source_document_parsed_event_is_emitted() -> None:
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(ledger=ledger)
    doc = SourceDocument(document_id="doc_a", content="Water boils at 100C.",
                         content_type="text/plain")
    adapter.project_document(doc)
    parsed = ledger.filter(LedgerEventType.SOURCE_DOCUMENT_PARSED)
    assert len(parsed) == 1
    payload = parsed[0].payload
    assert payload["document_id"] == "doc_a"
    assert payload["content_type"] == "text/plain"
    assert payload["text_length"] > 0
    assert payload["parser_version"] == "v1.1"
    assert payload["parser_hash"].startswith("pa_")


# ---------------------------------------------------------------------------
# LLM request start / response accepted
# ---------------------------------------------------------------------------


def _ok_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [{"canonical_content": "water boils at 100°C",
                    "raw_span": "Water boils at 100C.",
                    "confidence": 0.9, "ambiguous": False,
                    "proposed_relations": []}],
    })


def test_successful_llm_call_emits_started_and_accepted(
    monkeypatch,
) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_ok_llm_call),
        ledger=ledger,
    )
    adapter.project_text("Water boils at 100C.")
    started = ledger.filter(LedgerEventType.LLM_REQUEST_STARTED)
    accepted = ledger.filter(LedgerEventType.LLM_RESPONSE_ACCEPTED)
    assert len(started) == 1
    assert started[0].payload["model_name"] == "deepseek-4-pro"
    assert len(accepted) == 1
    assert accepted[0].payload["size_bytes"] > 0
    assert accepted[0].payload["output_hash"].startswith("oh_")


def test_llm_request_failed_emitted_on_network_error(monkeypatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")
    ledger = EvolutionLedger(version="v1.1")

    def _timeout(prompt: str) -> str:
        raise TimeoutError("boom")

    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_timeout), ledger=ledger,
    )
    adapter.project_text("Water boils at 100C.")
    failed = ledger.filter(LedgerEventType.LLM_REQUEST_FAILED)
    assert len(failed) == 1
    assert failed[0].payload["reason"] == "llm_call_failed"
    assert "retry_count" in failed[0].payload


def test_llm_response_rejected_emitted_on_invalid_json(monkeypatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")
    ledger = EvolutionLedger(version="v1.1")

    def _bad_json(prompt: str) -> str:
        return "not actually json"

    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_bad_json), ledger=ledger,
    )
    adapter.project_text("Water boils at 100C.")
    rejected = ledger.filter(LedgerEventType.LLM_RESPONSE_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "invalid_json"


# ---------------------------------------------------------------------------
# JSONL append-only persistence for the new events
# ---------------------------------------------------------------------------


def test_v11_events_persist_jsonl_and_replay(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    ledger = EvolutionLedgerJSONL(p, version="v1.1")
    adapter = SPLAdapter(ledger=ledger)
    doc = SourceDocument(document_id="doc_a", content="Water boils at 100C.",
                         content_type="text/plain")
    adapter.project_document(doc)
    n_before = len(ledger.entries())

    # Reopen.
    ledger_b = EvolutionLedgerJSONL(p, version="v1.1")
    assert len(ledger_b.entries()) == n_before


def test_v11_events_have_deterministic_payload_hash(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v1.1")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v1.1")
    payload = {
        "document_id": "doc_a",
        "content_type": "text/plain",
        "text_length": 20,
        "parser_version": "v1.1",
        "parser_hash": "pa_deadbeefdeadbeef",
    }
    ea = a.append(LedgerEventType.SOURCE_DOCUMENT_PARSED, payload)
    eb = b.append(LedgerEventType.SOURCE_DOCUMENT_PARSED, payload)
    assert ea.payload_hash == eb.payload_hash
