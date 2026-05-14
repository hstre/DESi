"""Tests for SourceDocument — v1.1 structured input."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from desi.spl_adapter import (
    SUPPORTED_CONTENT_TYPES,
    SourceDocument,
)


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


def test_document_id_is_required() -> None:
    with pytest.raises(ValueError):
        SourceDocument(document_id="", content="x", content_type="text/plain")


def test_content_type_is_required() -> None:
    with pytest.raises(ValueError):
        SourceDocument(document_id="d", content="x", content_type="")


# ---------------------------------------------------------------------------
# Type-aware content checks
# ---------------------------------------------------------------------------


def test_pdf_requires_bytes_content() -> None:
    with pytest.raises(TypeError):
        SourceDocument(document_id="d", content="not bytes",
                       content_type="application/pdf")


def test_text_types_require_str_content() -> None:
    with pytest.raises(TypeError):
        SourceDocument(document_id="d", content=b"bytes",
                       content_type="text/plain")


def test_html_requires_str_content() -> None:
    with pytest.raises(TypeError):
        SourceDocument(document_id="d", content=b"<html/>",
                       content_type="text/html")


# ---------------------------------------------------------------------------
# Supported MIME types form a closed set
# ---------------------------------------------------------------------------


def test_supported_content_types_is_a_closed_set() -> None:
    assert SUPPORTED_CONTENT_TYPES == frozenset({
        "text/plain", "text/markdown", "text/html", "application/pdf",
    })


def test_is_supported_for_known_types() -> None:
    for ct in ("text/plain", "text/markdown", "text/html"):
        doc = SourceDocument(document_id="d", content="x", content_type=ct)
        assert doc.is_supported


def test_is_supported_false_for_unknown_type() -> None:
    doc = SourceDocument(document_id="d", content="x",
                         content_type="text/csv")
    assert not doc.is_supported


# ---------------------------------------------------------------------------
# Audit shape
# ---------------------------------------------------------------------------


def test_to_dict_excludes_content_body() -> None:
    """The content payload may be large or sensitive; the audit dict
    contains only metadata."""
    doc = SourceDocument(
        document_id="doc_abc", content="a lot of text",
        content_type="text/plain", author="alice", language="en",
    )
    d = doc.to_dict()
    assert "content" not in d
    assert d["document_id"] == "doc_abc"
    assert d["content_type"] == "text/plain"
    assert d["author"] == "alice"
    assert d["language"] == "en"
    assert d["content_size"] == len("a lot of text")


def test_created_at_defaults_to_now() -> None:
    doc = SourceDocument(document_id="d", content="x",
                         content_type="text/plain")
    assert isinstance(doc.created_at, datetime)
    assert doc.created_at.tzinfo is not None


def test_created_at_is_preserved_when_supplied() -> None:
    when = datetime(2024, 1, 1, tzinfo=timezone.utc)
    doc = SourceDocument(document_id="d", content="x",
                         content_type="text/plain", created_at=when)
    assert doc.created_at == when


# ---------------------------------------------------------------------------
# Frozen dataclass — no in-place mutation
# ---------------------------------------------------------------------------


def test_source_document_is_frozen() -> None:
    doc = SourceDocument(document_id="d", content="x",
                         content_type="text/plain")
    with pytest.raises(Exception):
        doc.content = "tampered"  # type: ignore
