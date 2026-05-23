"""Tests for the LLM backend provenance — all mandatory fields populated."""
from __future__ import annotations

import json

import pytest

from desi.spl_adapter import (
    DEEPSEEK_MODEL_NAME,
    LLMSemanticBackend,
    SPLAdapter,
)


def _fake_llm_call(prompt: str) -> str:
    return json.dumps({
        "units": [
            {"canonical_content": "water boils at 100°C",
             "raw_span": "Water boils at 100C.",
             "confidence": 0.9, "ambiguous": False,
             "proposed_relations": []}
        ]
    })


# ---------------------------------------------------------------------------
# Backend constants are pinned to DeepSeek
# ---------------------------------------------------------------------------


def test_deepseek_is_the_only_model_name() -> None:
    assert DEEPSEEK_MODEL_NAME == "deepseek-4-pro"


def test_llm_backend_is_disabled_by_default() -> None:
    """Without an injected llm_call the backend fail-closes on use."""
    backend = LLMSemanticBackend()
    from desi.spl_adapter import BackendError
    with pytest.raises(BackendError):
        backend.extract_units("Water boils at 100C.")


# ---------------------------------------------------------------------------
# DeepSeek provenance is complete
# ---------------------------------------------------------------------------


def test_llm_provenance_carries_all_seven_mandatory_fields() -> None:
    backend = LLMSemanticBackend(
        llm_call=_fake_llm_call, temperature=0.2, max_tokens=256,
    )
    units = backend.extract_units("Water boils at 100C.")
    cands = backend.project_units(units, document_id="doc_abc",
                                   author="alice", language="en")
    assert len(cands) == 1
    prov = cands[0].spl_provenance
    assert prov.source == "spl_llm"
    assert prov.model_name == "deepseek-4-pro"
    assert prov.model_version  # non-empty
    assert prov.prompt_hash.startswith("ph_")
    assert prov.temperature == 0.2
    assert prov.max_tokens == 256
    assert prov.timestamp is not None
    assert prov.output_hash.startswith("oh_")
    assert prov.is_complete_llm_record


def test_provenance_propagates_optional_caller_metadata() -> None:
    backend = LLMSemanticBackend(llm_call=_fake_llm_call)
    units = backend.extract_units("Water boils at 100C.")
    cands = backend.project_units(
        units, document_id="doc_42", author="bob", language="de",
    )
    p = cands[0].spl_provenance
    assert p.document_id == "doc_42"
    assert p.author == "bob"
    assert p.language == "de"


def test_provenance_hashes_are_deterministic() -> None:
    """Same prompt + same output → same prompt_hash / output_hash."""
    a = LLMSemanticBackend(llm_call=_fake_llm_call)
    b = LLMSemanticBackend(llm_call=_fake_llm_call)
    units_a = a.extract_units("Water boils at 100C.")
    units_b = b.extract_units("Water boils at 100C.")
    cands_a = a.project_units(units_a)
    cands_b = b.project_units(units_b)
    assert cands_a[0].spl_provenance.prompt_hash == \
        cands_b[0].spl_provenance.prompt_hash
    assert cands_a[0].spl_provenance.output_hash == \
        cands_b[0].spl_provenance.output_hash


def test_provenance_to_dict_includes_all_fields() -> None:
    backend = LLMSemanticBackend(llm_call=_fake_llm_call)
    units = backend.extract_units("Water boils at 100C.")
    cands = backend.project_units(units)
    d = cands[0].spl_provenance.to_dict()
    for key in ("source", "model_name", "model_version", "prompt_hash",
                "temperature", "max_tokens", "timestamp", "output_hash"):
        assert key in d


# ---------------------------------------------------------------------------
# Deterministic backend has source="spl_deterministic" (no LLM fields)
# ---------------------------------------------------------------------------


def test_deterministic_backend_provenance_uses_spl_deterministic_source() -> None:
    adapter = SPLAdapter()
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
    assert result.claims[0].provenance.source == "spl_deterministic"


def test_llm_backend_provenance_uses_spl_llm_source() -> None:
    backend = LLMSemanticBackend(llm_call=_fake_llm_call)
    adapter = SPLAdapter(backend=backend)
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
    assert result.claims[0].provenance.source == "spl_llm"
