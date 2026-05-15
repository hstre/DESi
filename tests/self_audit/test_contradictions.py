"""Tests for v3.0 contradiction detector (Aufgabe 5)."""
from __future__ import annotations

from desi.self_audit import (
    ClaimKind,
    ExplicitClaim,
    find_contradictions,
)


def _c(doc, key, value, artifact=""):
    return ExplicitClaim(
        claim_id=f"cl_{doc}_{key}_{value}",
        doc_id=f"doc_{doc}", doc_path=doc, line_number=1,
        line_text="", kind=ClaimKind.NUMERIC, key=key,
        value=value, referenced_artifact=artifact,
    )


def test_no_contradiction_when_values_match() -> None:
    out = find_contradictions((
        _c("a.md", "precision", "1.0"),
        _c("a.md", "precision", "1.0"),
    ))
    assert out == ()


def test_within_document_contradiction_detected() -> None:
    out = find_contradictions((
        _c("a.md", "precision", "1.0"),
        _c("a.md", "precision", "0.99"),
    ))
    assert any(c.scope == "document:a.md" for c in out)
    assert any(c.key == "precision" for c in out)


def test_across_corpus_artifact_contradiction_detected() -> None:
    out = find_contradictions((
        _c("a.md", "precision", "1.0", artifact="artifacts/x.json"),
        _c("b.md", "precision", "0.99", artifact="artifacts/x.json"),
    ))
    artifact_scoped = [c for c in out if c.scope.startswith("artifact:")]
    assert artifact_scoped


def test_empty_key_excluded() -> None:
    out = find_contradictions((
        _c("a.md", "", "1.0"),
        _c("a.md", "", "0.99"),
    ))
    assert out == ()


def test_contradiction_to_dict_shape() -> None:
    out = find_contradictions((
        _c("a.md", "precision", "1.0"),
        _c("a.md", "precision", "0.99"),
    ))
    assert out
    d = out[0].to_dict()
    for k in ("key", "scope", "values", "claim_ids"):
        assert k in d


def test_detector_is_deterministic() -> None:
    claims = (
        _c("a.md", "precision", "1.0"),
        _c("a.md", "precision", "0.99"),
    )
    assert find_contradictions(claims) == find_contradictions(claims)
