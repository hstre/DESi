"""Tests for v3.0 historical drift detector (Aufgabe 6)."""
from __future__ import annotations

from desi.self_audit import ClaimKind, ExplicitClaim, find_drift


def _c(doc, key, value, artifact):
    return ExplicitClaim(
        claim_id=f"cl_{doc}_{key}_{value}",
        doc_id=f"doc_{doc}", doc_path=doc, line_number=1,
        line_text="", kind=ClaimKind.NUMERIC, key=key,
        value=value, referenced_artifact=artifact,
    )


def test_drift_detected_across_versions() -> None:
    out = find_drift((
        _c("docs/memory/v2_5.md", "precision", "1.000",
           "artifacts/v2_5/report.json"),
        _c("docs/memory/v2_7.md", "precision", "0.99",
           "artifacts/v2_5/report.json"),
    ))
    assert out
    assert out[0].earlier_value == "1.000"
    assert out[0].later_value == "0.99"


def test_no_drift_when_values_constant() -> None:
    out = find_drift((
        _c("docs/memory/v2_5.md", "precision", "1.000",
           "artifacts/v2_5/report.json"),
        _c("docs/memory/v2_7.md", "precision", "1.000",
           "artifacts/v2_5/report.json"),
    ))
    assert out == ()


def test_drift_requires_referenced_artifact() -> None:
    out = find_drift((
        _c("docs/memory/v2_5.md", "precision", "1.000", ""),
        _c("docs/memory/v2_7.md", "precision", "0.99", ""),
    ))
    assert out == ()


def test_drift_to_dict_shape() -> None:
    out = find_drift((
        _c("docs/memory/v2_5.md", "precision", "1.000",
           "artifacts/v2_5/report.json"),
        _c("docs/memory/v2_7.md", "precision", "0.99",
           "artifacts/v2_5/report.json"),
    ))
    assert out
    d = out[0].to_dict()
    for k in ("key", "artifact", "earlier_doc",
              "earlier_value", "later_doc", "later_value"):
        assert k in d


def test_drift_ordered_by_version() -> None:
    """v2.5 sorts before v2.7; the finding lists v2.5 as earlier."""
    out = find_drift((
        _c("docs/memory/v2_7.md", "precision", "0.99",
           "artifacts/x.json"),
        _c("docs/memory/v2_5.md", "precision", "1.000",
           "artifacts/x.json"),
    ))
    assert out
    assert out[0].earlier_doc.endswith("v2_5.md")
    assert out[0].later_doc.endswith("v2_7.md")
