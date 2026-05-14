"""DocumentParser — normalises a :class:`SourceDocument` to plain text.

v1.1 supports four input types:

* ``text/plain``     — returned verbatim, stripped of leading/trailing
                        whitespace.
* ``text/markdown``  — markdown markers removed (headings, emphasis,
                        list bullets, code fences). The semantic
                        content survives; the formatting does not.
* ``text/html``      — every ``<script>`` and ``<style>`` block is
                        discarded; remaining tags are stripped; HTML
                        entities are decoded.
* ``application/pdf`` — pure-Python text extraction from BT/ET blocks,
                        with ``FlateDecode`` support via ``zlib``. No
                        OCR, no font tables, no image extraction.

Every parser failure is converted to a ``BackendError`` and
fail-closes the projection. The parser never raises into the adapter.
"""
from __future__ import annotations

import hashlib
import html
import re
import zlib
from dataclasses import dataclass
from html.parser import HTMLParser

from .errors import BackendError
from .source import SUPPORTED_CONTENT_TYPES, SourceDocument


PARSER_VERSION = "v1.1"


# ---------------------------------------------------------------------------
# HTML stripper
# ---------------------------------------------------------------------------


class _HTMLTextExtractor(HTMLParser):
    """Strip ``<script>`` / ``<style>`` and keep visible text only."""

    _SKIP_TAGS: frozenset[str] = frozenset({"script", "style", "noscript"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._buf: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag.lower() in ("p", "br", "div", "li", "tr", "h1", "h2",
                              "h3", "h4", "h5", "h6"):
            self._buf.append("\n")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_startendtag(self, tag, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "br":
            self._buf.append("\n")

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth > 0:
            return
        self._buf.append(data)

    def text(self) -> str:
        raw = "".join(self._buf)
        # Decode any leftover entities (convert_charrefs handles most).
        raw = html.unescape(raw)
        return _normalise_whitespace(raw)


def _normalise_whitespace(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


# ---------------------------------------------------------------------------
# Markdown stripper
# ---------------------------------------------------------------------------


_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MD_ITAL = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_MD_INLINE_CODE = re.compile(r"`([^`]+?)`")
_MD_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_LIST = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_MD_ORDERED = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)


def _strip_markdown(text: str) -> str:
    out = _MD_CODE_FENCE.sub(" ", text)
    out = _MD_HEADING.sub("", out)
    out = _MD_BOLD.sub(r"\1", out)
    out = _MD_ITAL.sub(r"\1", out)
    out = _MD_INLINE_CODE.sub(r"\1", out)
    out = _MD_LINK.sub(r"\1", out)
    out = _MD_LIST.sub("", out)
    out = _MD_ORDERED.sub("", out)
    return _normalise_whitespace(out)


# ---------------------------------------------------------------------------
# PDF text extractor (pure Python, no OCR, no fonts)
# ---------------------------------------------------------------------------


_PDF_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream",
                         re.DOTALL)
_PDF_OBJ = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream",
                      re.DOTALL)
_PDF_TEXT_BLOCK = re.compile(rb"BT(.*?)ET", re.DOTALL)
# Match  (...) Tj    or    (...) TJ
_PDF_TJ_LITERAL = re.compile(rb"\((.*?)\)\s*T[Jj]", re.DOTALL)


def _extract_pdf_text(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise BackendError("pdf_parse_failed",
                            "PDF parser requires bytes input")
    if not data.startswith(b"%PDF"):
        raise BackendError("pdf_parse_failed",
                            "input does not start with %PDF header")
    # Walk every <<dict>> stream pair so we can detect FlateDecode.
    fragments: list[str] = []
    for match in _PDF_OBJ.finditer(data):
        header, body = match.group(1), match.group(2)
        is_flate = b"/FlateDecode" in header
        try:
            stream_data = zlib.decompress(body) if is_flate else body
        except zlib.error:
            # Skip streams we cannot decode (encrypted, malformed, etc.).
            continue
        for bt in _PDF_TEXT_BLOCK.finditer(stream_data):
            for lit in _PDF_TJ_LITERAL.finditer(bt.group(1)):
                fragments.append(_decode_pdf_literal(lit.group(1)))
    # Also handle streams that are not wrapped in our <<…>>stream pattern
    # (e.g. older PDFs that put the dictionary on a separate line).
    if not fragments:
        for stream_match in _PDF_STREAM.finditer(data):
            body = stream_match.group(1)
            for bt in _PDF_TEXT_BLOCK.finditer(body):
                for lit in _PDF_TJ_LITERAL.finditer(bt.group(1)):
                    fragments.append(_decode_pdf_literal(lit.group(1)))
    return _normalise_whitespace(" ".join(fragments))


_PDF_ESCAPES = {
    b"\\n": b"\n",
    b"\\r": b"\r",
    b"\\t": b"\t",
    b"\\b": b"\b",
    b"\\f": b"\f",
    b"\\(": b"(",
    b"\\)": b")",
    b"\\\\": b"\\",
}


def _decode_pdf_literal(raw: bytes) -> str:
    out = raw
    for k, v in _PDF_ESCAPES.items():
        out = out.replace(k, v)
    try:
        return out.decode("utf-8", errors="replace")
    except Exception:
        return out.decode("latin-1", errors="replace")


# ---------------------------------------------------------------------------
# Public parser
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParseResult:
    """Output of :meth:`DocumentParser.parse`."""

    normalized_text: str
    parser_version: str
    parser_hash: str
    document_id: str
    content_type: str


class DocumentParser:
    """Normalise a :class:`SourceDocument` to plain text.

    The parser is stateless and deterministic: same input bytes →
    same ``normalized_text`` and same ``parser_hash``.
    """

    @property
    def version(self) -> str:
        return PARSER_VERSION

    def parse(self, doc: SourceDocument) -> ParseResult:
        if not doc.is_supported:
            raise BackendError(
                "unsupported_document_type",
                f"content_type={doc.content_type!r} is not in the v1.1 "
                f"supported set {sorted(SUPPORTED_CONTENT_TYPES)}",
            )
        if doc.content_size == 0:
            raise BackendError("empty_document",
                                f"document {doc.document_id} has no content")
        if doc.content_type == "text/plain":
            text = _normalise_whitespace(str(doc.content))
        elif doc.content_type == "text/markdown":
            text = _strip_markdown(str(doc.content))
        elif doc.content_type == "text/html":
            extractor = _HTMLTextExtractor()
            extractor.feed(str(doc.content))
            extractor.close()
            text = extractor.text()
        elif doc.content_type == "application/pdf":
            text = _extract_pdf_text(bytes(doc.content))
        else:  # pragma: no cover — guarded by is_supported above
            raise BackendError("unsupported_document_type",
                                doc.content_type)
        if not text:
            raise BackendError("empty_document",
                                f"document {doc.document_id} parsed to "
                                "empty text")
        return ParseResult(
            normalized_text=text,
            parser_version=PARSER_VERSION,
            parser_hash=_parser_hash(text),
            document_id=doc.document_id,
            content_type=doc.content_type,
        )


def _parser_hash(text: str) -> str:
    raw = text.encode("utf-8")
    return "pa_" + hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "DocumentParser",
    "PARSER_VERSION",
    "ParseResult",
]
