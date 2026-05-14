"""Tests for DocumentParser — text/markdown/html/pdf normalisation."""
from __future__ import annotations

import zlib

import pytest

from desi.spl_adapter import (
    BackendError,
    DocumentParser,
    SourceDocument,
)


def _parser() -> DocumentParser:
    return DocumentParser()


# ---------------------------------------------------------------------------
# text/plain
# ---------------------------------------------------------------------------


def test_plain_text_passes_through_with_normalisation() -> None:
    doc = SourceDocument(document_id="d", content="  Water boils at 100C.  ",
                         content_type="text/plain")
    result = _parser().parse(doc)
    assert result.normalized_text == "Water boils at 100C."


def test_parser_version_and_hash_are_set() -> None:
    doc = SourceDocument(document_id="d", content="x",
                         content_type="text/plain")
    result = _parser().parse(doc)
    assert result.parser_version == "v1.1"
    assert result.parser_hash.startswith("pa_")
    assert len(result.parser_hash) == 19  # "pa_" + 16 hex chars


def test_parser_hash_is_deterministic_on_same_text() -> None:
    doc1 = SourceDocument(document_id="d1", content="Water boils at 100C.",
                          content_type="text/plain")
    doc2 = SourceDocument(document_id="d2", content="Water boils at 100C.",
                          content_type="text/plain")
    a = _parser().parse(doc1)
    b = _parser().parse(doc2)
    assert a.parser_hash == b.parser_hash


# ---------------------------------------------------------------------------
# text/markdown
# ---------------------------------------------------------------------------


def test_markdown_removes_headings_and_emphasis() -> None:
    md = (
        "# Boiling point\n\n"
        "**Water** boils at *100C* under standard pressure.\n"
        "\n"
        "- one bullet\n"
        "1. one number\n"
    )
    doc = SourceDocument(document_id="d", content=md,
                         content_type="text/markdown")
    text = _parser().parse(doc).normalized_text
    assert "#" not in text
    assert "**" not in text
    assert "*" not in text
    assert "Water boils at 100C" in text


def test_markdown_removes_code_fences() -> None:
    md = "Plain.\n```python\ndef f(): pass\n```\nMore plain."
    doc = SourceDocument(document_id="d", content=md,
                         content_type="text/markdown")
    text = _parser().parse(doc).normalized_text
    assert "def f" not in text
    assert "Plain." in text
    assert "More plain." in text


def test_markdown_keeps_link_text_drops_url() -> None:
    md = "See [reference](https://example.com/x.html) for details."
    doc = SourceDocument(document_id="d", content=md,
                         content_type="text/markdown")
    text = _parser().parse(doc).normalized_text
    assert "reference" in text
    assert "https://example.com" not in text


# ---------------------------------------------------------------------------
# text/html
# ---------------------------------------------------------------------------


def test_html_strips_script_and_style() -> None:
    html_doc = (
        "<html><head>"
        "<style>body { color: red; }</style>"
        "<script>analytics.track('pageview');</script>"
        "</head><body><p>Water boils at 100C.</p></body></html>"
    )
    doc = SourceDocument(document_id="d", content=html_doc,
                         content_type="text/html")
    text = _parser().parse(doc).normalized_text
    assert "analytics" not in text
    assert "color: red" not in text
    assert "Water boils at 100C." in text


def test_html_decodes_entities() -> None:
    html_doc = "<p>Water boils &gt; 99&deg;C.</p>"
    doc = SourceDocument(document_id="d", content=html_doc,
                         content_type="text/html")
    text = _parser().parse(doc).normalized_text
    assert "Water boils > 99°C." in text


def test_html_keeps_text_across_block_elements() -> None:
    html_doc = "<div>Water</div><div>boils at</div><div>100C.</div>"
    doc = SourceDocument(document_id="d", content=html_doc,
                         content_type="text/html")
    text = _parser().parse(doc).normalized_text
    assert "Water" in text and "boils at" in text and "100C." in text


# ---------------------------------------------------------------------------
# application/pdf
# ---------------------------------------------------------------------------


def _make_minimal_pdf(text: str = "Water boils at 100C.") -> bytes:
    """Hand-craft a minimal PDF whose only stream contains BT/ET text."""
    payload = (
        f"BT\n/F1 12 Tf\n72 720 Td\n({text}) Tj\nET\n".encode("utf-8")
    )
    header = b"%PDF-1.4\n"
    body = (
        b"1 0 obj <</Length "
        + str(len(payload)).encode()
        + b">>\nstream\n"
        + payload
        + b"\nendstream\nendobj\n"
    )
    return header + body


def test_pdf_extracts_text_from_uncompressed_stream() -> None:
    pdf = _make_minimal_pdf("Water boils at 100C.")
    doc = SourceDocument(document_id="d", content=pdf,
                         content_type="application/pdf")
    text = _parser().parse(doc).normalized_text
    assert "Water boils at 100C." in text


def test_pdf_extracts_text_from_flate_compressed_stream() -> None:
    raw_stream = b"BT\n/F1 12 Tf\n(Water boils at 100C.) Tj\nET\n"
    compressed = zlib.compress(raw_stream)
    pdf = (
        b"%PDF-1.4\n1 0 obj <</Length "
        + str(len(compressed)).encode()
        + b" /Filter /FlateDecode>>\nstream\n"
        + compressed
        + b"\nendstream\nendobj\n"
    )
    doc = SourceDocument(document_id="d", content=pdf,
                         content_type="application/pdf")
    text = _parser().parse(doc).normalized_text
    assert "Water boils at 100C." in text


def test_pdf_without_header_is_rejected() -> None:
    doc = SourceDocument(document_id="d", content=b"not a pdf",
                         content_type="application/pdf")
    with pytest.raises(BackendError) as exc:
        _parser().parse(doc)
    assert exc.value.kind == "pdf_parse_failed"


def test_empty_pdf_streams_yield_empty_document_error() -> None:
    """A PDF with the right header but no text streams parses to
    empty text → fail-closed with empty_document."""
    pdf = b"%PDF-1.4\n%\xC4\xE5\xF2\xE5\xEB\xA7\n"
    doc = SourceDocument(document_id="d", content=pdf,
                         content_type="application/pdf")
    with pytest.raises(BackendError) as exc:
        _parser().parse(doc)
    assert exc.value.kind == "empty_document"


# ---------------------------------------------------------------------------
# Unsupported types fail-close with a distinct kind
# ---------------------------------------------------------------------------


def test_unsupported_type_raises_with_known_kind() -> None:
    doc = SourceDocument(document_id="d", content="x",
                         content_type="application/x-strange")
    with pytest.raises(BackendError) as exc:
        _parser().parse(doc)
    assert exc.value.kind == "unsupported_document_type"


def test_empty_text_document_is_rejected() -> None:
    doc = SourceDocument(document_id="d", content="   \n\n   ",
                         content_type="text/plain")
    with pytest.raises(BackendError) as exc:
        _parser().parse(doc)
    assert exc.value.kind == "empty_document"
