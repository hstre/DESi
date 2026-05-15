"""Tests for v3.1 anchor schema + parser (Aufgabe 1)."""
from __future__ import annotations

from desi.doc_anchors import (
    ANCHOR_PREFIX,
    ClaimAnchor,
    LEGACY_MARKER,
    LegacyExemption,
    parse_anchors,
    parse_legacy_markers,
)


def test_anchor_prefix_is_canonical() -> None:
    assert ANCHOR_PREFIX == "[claim-anchor:"


def test_legacy_marker_is_canonical() -> None:
    assert LEGACY_MARKER == "[legacy-unanchored]"


def test_parser_extracts_single_line_anchor() -> None:
    text = (
        "precision: 1.000 "
        "[claim-anchor: artifact=artifacts/x.json, "
        "field=metrics.precision, expected=1.000]"
    )
    anchors = parse_anchors("t.md", text)
    assert len(anchors) == 1
    a = anchors[0]
    assert a.artifact == "artifacts/x.json"
    assert a.field == "metrics.precision"
    assert a.expected == "1.000"


def test_parser_is_whitespace_tolerant() -> None:
    text = "[claim-anchor:artifact=x.json,field=k,expected=v]"
    anchors = parse_anchors("t.md", text)
    assert len(anchors) == 1
    assert anchors[0].artifact == "x.json"


def test_parser_skips_malformed_anchor() -> None:
    text = "[claim-anchor: artifact=x.json]"   # missing field
    anchors = parse_anchors("t.md", text)
    assert anchors == ()


def test_parser_picks_up_legacy_marker() -> None:
    text = "Some prose\n[legacy-unanchored]\nMore prose\n"
    marks = parse_legacy_markers("t.md", text)
    assert len(marks) == 1
    assert isinstance(marks[0], LegacyExemption)


def test_parser_is_case_sensitive_on_keys() -> None:
    """Lowercase ``artifact`` is required; ``ARTIFACT`` is ignored."""
    text = "[claim-anchor: ARTIFACT=x.json, FIELD=k, EXPECTED=v]"
    anchors = parse_anchors("t.md", text)
    assert anchors == ()


def test_claim_anchor_to_dict_shape() -> None:
    a = ClaimAnchor(
        artifact="x.json", field="k", expected="v",
        doc_path="t.md", line_number=1, raw="...",
    )
    d = a.to_dict()
    for k in ("artifact", "field", "expected", "doc_path", "line_number"):
        assert k in d
