"""Tests for the v3.0 corpus indexer (Aufgabe 1)."""
from __future__ import annotations

import pathlib

from desi.self_audit import (
    DocumentArtifact,
    REQUIRED_MEMORY_DOCS,
    REQUIRED_PROTOCOL_DOCS,
    index_corpus,
    index_document,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_corpus_contains_every_required_memory_doc() -> None:
    corpus = index_corpus(_REPO_ROOT)
    indexed_names = {pathlib.Path(d.path).name for d in corpus}
    for required in REQUIRED_MEMORY_DOCS:
        assert required in indexed_names, f"missing {required}"


def test_corpus_contains_every_required_protocol_doc() -> None:
    corpus = index_corpus(_REPO_ROOT)
    paths = {d.path for d in corpus}
    for fname in REQUIRED_PROTOCOL_DOCS:
        assert any(p.endswith(f"rule_patch_protocol/{fname}") for p in paths)


def test_document_artifact_fields_present() -> None:
    corpus = index_corpus(_REPO_ROOT)
    assert corpus
    doc = corpus[0]
    assert isinstance(doc, DocumentArtifact)
    for f in ("doc_id", "path", "sha256", "line_count", "section_count"):
        assert hasattr(doc, f)


def test_sha256_is_sixteen_hex_chars() -> None:
    corpus = index_corpus(_REPO_ROOT)
    for d in corpus:
        assert len(d.sha256) == 16
        int(d.sha256, 16)


def test_doc_id_is_deterministic() -> None:
    a = index_document(_REPO_ROOT, "docs/memory/v2_8.md")
    b = index_document(_REPO_ROOT, "docs/memory/v2_8.md")
    assert a.doc_id == b.doc_id
    assert a.sha256 == b.sha256


def test_doc_ids_unique_across_corpus() -> None:
    corpus = index_corpus(_REPO_ROOT)
    ids = [d.doc_id for d in corpus]
    assert len(set(ids)) == len(ids)


def test_to_dict_round_trip_shape() -> None:
    d = index_document(_REPO_ROOT, "docs/memory/v2_8.md")
    payload = d.to_dict()
    for k in ("doc_id", "path", "sha256", "line_count", "section_count"):
        assert k in payload
