"""D1–D8 — the v1.1 evaluation scenarios.

* **D1 Plain text**         — projection succeeds
* **D2 Markdown**           — projection succeeds, markdown markers stripped
* **D3 HTML noise**         — tracking / JS / CSS removed before projection
* **D4 Empty PDF**          — fail-closed, ``empty_document``
* **D5 Timeout**            — fail-closed, ``timeout`` (LLM_REQUEST_FAILED)
* **D6 Malformed JSON**     — fail-closed, ``invalid_json``
                              (LLM_RESPONSE_REJECTED)
* **D7 Oversized JSON**     — fail-closed, ``response_too_large``
                              (LLM_RESPONSE_REJECTED)
* **D8 Missing key**        — fail-closed, ``missing_api_key``
"""
from __future__ import annotations

import json
import zlib

import pytest

from desi.evolution import EvolutionLedger, LedgerEventType
from desi.spl_adapter import (
    DeepSeekClient,
    LLMSemanticBackend,
    MAX_LLM_RESPONSE_BYTES,
    SourceDocument,
    SPLAdapter,
)
from desi.spl_adapter.deepseek_client import API_KEY_ENV_VAR


# ---------------------------------------------------------------------------
# D1 — Plain text
# ---------------------------------------------------------------------------


def test_d1_plain_text_projection_succeeds() -> None:
    doc = SourceDocument(
        document_id="d1", content="Water boils at 100C.",
        content_type="text/plain", author="alice", language="en",
    )
    result = SPLAdapter().project_document(doc)
    assert len(result.claims) == 1
    assert result.claims[0].content == "water boils at 100°C"


# ---------------------------------------------------------------------------
# D2 — Markdown
# ---------------------------------------------------------------------------


def test_d2_markdown_projection_succeeds_without_markers() -> None:
    md = (
        "# Boiling Point\n\n"
        "**Water** boils at *100C* at standard pressure.\n"
        "\n"
        "See [a reference](https://example.com)."
    )
    doc = SourceDocument(document_id="d2", content=md,
                         content_type="text/markdown")
    result = SPLAdapter().project_document(doc)
    assert len(result.claims) == 1
    assert result.claims[0].content == "water boils at 100°C"


# ---------------------------------------------------------------------------
# D3 — HTML noise
# ---------------------------------------------------------------------------


def test_d3_html_noise_is_stripped_before_projection() -> None:
    html_doc = (
        "<html><head>"
        "<script>analytics.track('pageview');</script>"
        "<style>body { display: none; }</style>"
        "</head><body><p>Water boils at 100C.</p></body></html>"
    )
    doc = SourceDocument(document_id="d3", content=html_doc,
                         content_type="text/html")
    result = SPLAdapter().project_document(doc)
    assert len(result.claims) == 1
    assert result.claims[0].content == "water boils at 100°C"


# ---------------------------------------------------------------------------
# D4 — Empty PDF
# ---------------------------------------------------------------------------


def test_d4_empty_pdf_fail_closes() -> None:
    pdf = b"%PDF-1.4\n%\xC4\xE5\xF2\xE5\xEB\xA7\n"
    doc = SourceDocument(document_id="d4", content=pdf,
                         content_type="application/pdf")
    result = SPLAdapter().project_document(doc)
    assert result.claims == ()
    assert result.backend_error == "empty_document"


# ---------------------------------------------------------------------------
# D5 — Timeout
# ---------------------------------------------------------------------------


def test_d5_timeout_fail_closes_with_request_failed(monkeypatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")

    def _timeout(req, timeout):
        raise TimeoutError("read timed out")

    client = DeepSeekClient(transport=_timeout, sleep_fn=lambda s: None)
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=client), ledger=ledger,
    )
    doc = SourceDocument(document_id="d5", content="Water boils at 100C.",
                         content_type="text/plain")
    result = adapter.project_document(doc)
    assert result.claims == ()
    assert result.backend_error == "timeout"
    failed = ledger.filter(LedgerEventType.LLM_REQUEST_FAILED)
    assert len(failed) == 1
    assert failed[0].payload["reason"] == "timeout"


# ---------------------------------------------------------------------------
# D6 — Malformed JSON
# ---------------------------------------------------------------------------


def test_d6_malformed_json_fail_closes_with_response_rejected(
    monkeypatch,
) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")

    def _bad_json(req, timeout):
        return b"not actually json {"

    client = DeepSeekClient(transport=_bad_json)
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=client), ledger=ledger,
    )
    doc = SourceDocument(document_id="d6", content="Water boils at 100C.",
                         content_type="text/plain")
    result = adapter.project_document(doc)
    assert result.claims == ()
    assert result.backend_error == "invalid_json"
    rejected = ledger.filter(LedgerEventType.LLM_RESPONSE_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "invalid_json"


# ---------------------------------------------------------------------------
# D7 — Oversized JSON
# ---------------------------------------------------------------------------


def test_d7_oversized_json_fail_closes_at_the_client(monkeypatch) -> None:
    """The client's transport-level guard fires first (the client
    refuses to return bytes beyond 50 KB), so the kind reported is
    `response_too_large`."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake")
    giant = b"x" * (MAX_LLM_RESPONSE_BYTES + 100)

    def _big(req, timeout):
        return giant

    client = DeepSeekClient(transport=_big, sleep_fn=lambda s: None)
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=client), ledger=ledger,
    )
    doc = SourceDocument(document_id="d7", content="Water boils at 100C.",
                         content_type="text/plain")
    result = adapter.project_document(doc)
    assert result.claims == ()
    assert result.backend_error == "response_too_large"
    rejected = ledger.filter(LedgerEventType.LLM_RESPONSE_REJECTED)
    assert any(r.payload["reason"] == "response_too_large" for r in rejected)


# ---------------------------------------------------------------------------
# D8 — Missing key
# ---------------------------------------------------------------------------


def test_d8_missing_api_key_fail_closes(monkeypatch) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    def _should_not_be_called(req, timeout):
        raise AssertionError("transport must not be invoked without key")

    client = DeepSeekClient(transport=_should_not_be_called)
    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=client), ledger=ledger,
    )
    doc = SourceDocument(document_id="d8", content="Water boils at 100C.",
                         content_type="text/plain")
    result = adapter.project_document(doc)
    assert result.claims == ()
    assert result.backend_error == "missing_api_key"


def test_d8_no_key_does_not_leak_anywhere_into_ledger(monkeypatch) -> None:
    """The ledger never contains the API key (it isn't set, but assert
    the negative: no payload string contains a key-like substring)."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    def _no_call(req, timeout):
        return b"{}"

    ledger = EvolutionLedger(version="v1.1")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=DeepSeekClient(transport=_no_call)),
        ledger=ledger,
    )
    doc = SourceDocument(document_id="d8b", content="Water boils at 100C.",
                         content_type="text/plain")
    adapter.project_document(doc)
    for entry in ledger.entries():
        flat = json.dumps(entry.to_dict())
        assert "sk-" not in flat
        assert "DEEPSEEK_API_KEY" not in flat
